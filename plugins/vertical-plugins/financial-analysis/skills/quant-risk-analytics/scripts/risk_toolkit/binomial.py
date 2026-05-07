"""Binomial tree option pricing utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional
import math

import numpy as np

from .errors import TaskInputError
from .options import bsm_price


def _tree_params(n: int, rate: float, vol: float, tau: float, tree: str, div_yield: float) -> tuple[float, float, float]:
    dt = tau / n
    tree = tree.upper()
    if tree == "CRR":
        u = math.exp(vol * math.sqrt(dt))
        d = 1.0 / u
        p = (math.exp((rate - div_yield) * dt) - d) / (u - d)
    elif tree == "JD":
        u = math.exp((rate - div_yield - 0.5 * vol**2) * dt + vol * math.sqrt(dt))
        d = math.exp((rate - div_yield - 0.5 * vol**2) * dt - vol * math.sqrt(dt))
        p = 0.5
    elif tree == "LR":
        def h_function(z: float, n_steps: int) -> float:
            return 0.5 + math.copysign(1.0, z) * math.sqrt(
                0.25 - 0.25 * math.exp(-((z / (n_steps + 1.0 / 3.0 + 0.1 / (n_steps + 1.0))) ** 2) * (n_steps + 1.0 / 6.0))
            )

        n_bar = n if n % 2 else n + 1
        d1 = (math.log(1.0) + (rate - div_yield + 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
        d2 = d1 - vol * math.sqrt(tau)
        pbar = h_function(d1, n_bar)
        p = h_function(d2, n_bar)
        u = math.exp((rate - div_yield) * dt) * pbar / p
        d = (math.exp((rate - div_yield) * dt) - p * u) / (1.0 - p)
    else:
        raise TaskInputError("tree must be CRR, JD, or LR")
    if not 0.0 < p < 1.0:
        raise TaskInputError("Invalid risk-neutral probability")
    return u, d, p


def price(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    n = int(payload.get("steps", 0))
    spot = float(payload.get("spot", 0.0))
    strike = float(payload.get("strike", 0.0))
    rate = float(payload.get("rate", 0.0))
    vol = float(payload.get("vol", 0.0))
    tau = float(payload.get("tau", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    option_type = payload.get("option_type", "call").lower()
    exercise = payload.get("exercise", "european").lower()
    tree = payload.get("tree", "CRR")
    return_tree = bool(payload.get("return_tree", False))

    if n <= 0 or spot <= 0 or strike <= 0 or vol <= 0 or tau <= 0:
        raise TaskInputError("steps, spot, strike, vol, tau must be positive")
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")
    if exercise not in ("european", "american"):
        raise TaskInputError("exercise must be european or american")

    dt = tau / n
    u, d, p = _tree_params(n, rate, vol, tau, tree, div_yield)

    stock = np.zeros((n + 1, n + 1))
    stock[0, 0] = spot
    for i in range(1, n + 1):
        stock[i, 0] = stock[i - 1, 0] * u
        for j in range(1, i + 1):
            stock[i, j] = stock[i - 1, j - 1] * d

    option = np.zeros((n + 1, n + 1))
    for j in range(n + 1):
        if option_type == "call":
            option[n, j] = max(0.0, stock[n, j] - strike)
        else:
            option[n, j] = max(0.0, strike - stock[n, j])

    disc = math.exp(-rate * dt)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            continuation = disc * (p * option[i + 1, j] + (1.0 - p) * option[i + 1, j + 1])
            if exercise == "american":
                intrinsic = max(0.0, (stock[i, j] - strike) if option_type == "call" else (strike - stock[i, j]))
                option[i, j] = max(intrinsic, continuation)
            else:
                option[i, j] = continuation

    result = {
        "price": float(option[0, 0]),
        "artifacts": [],
        "warnings": [],
    }
    if return_tree:
        result["stock_tree"] = stock.tolist()
        result["option_tree"] = option.tolist()
    return result


def terminal_distribution(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    n = int(payload.get("steps", 0))
    spot = float(payload.get("spot", 0.0))
    rate = float(payload.get("rate", 0.0))
    vol = float(payload.get("vol", 0.0))
    tau = float(payload.get("tau", 0.0))
    tree = payload.get("tree", "CRR")
    div_yield = float(payload.get("div_yield", 0.0))
    if n <= 0 or spot <= 0 or vol <= 0 or tau <= 0:
        raise TaskInputError("steps, spot, vol, tau must be positive")

    u, d, p = _tree_params(n, rate, vol, tau, tree, div_yield)
    prices = []
    probs = []
    for j in range(n + 1):
        price = spot * (u ** (n - j)) * (d ** j)
        prob = math.comb(n, j) * (p ** (n - j)) * ((1.0 - p) ** j)
        prices.append(float(price))
        probs.append(float(prob))
    return {"prices": prices, "probabilities": probs, "artifacts": [], "warnings": []}


def convergence_vs_bsm(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    steps = payload.get("steps", list(range(2, 200, 5)))
    spot = float(payload.get("spot", 50.0))
    strike = float(payload.get("strike", 55.0))
    rate = float(payload.get("rate", 0.03))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.3))
    tau = float(payload.get("tau", 1.0))
    option_type = payload.get("option_type", "call").lower()
    tree = payload.get("tree", "CRR")

    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")

    bsm = bsm_price({"spot": spot, "strike": strike, "tau": tau, "rate": rate, "vol": vol, "div_yield": div_yield})
    bsm_value = float(bsm["call"] if option_type == "call" else bsm["put"])

    prices = []
    for n in steps:
        res = price(
            {
                "steps": int(n),
                "spot": spot,
                "strike": strike,
                "rate": rate,
                "vol": vol,
                "tau": tau,
                "div_yield": div_yield,
                "option_type": option_type,
                "exercise": "european",
                "tree": tree,
            }
        )
        prices.append(float(res["price"]))

    discrepancy = [(p / bsm_value - 1.0) * 100.0 for p in prices]
    return {
        "steps": [int(v) for v in steps],
        "binomial": prices,
        "bsm": bsm_value,
        "discrepancy_pct": discrepancy,
        "artifacts": [],
        "warnings": [],
    }


def price_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots = np.asarray(payload.get("spots", []), dtype=float)
    taus = np.asarray(payload.get("taus", []), dtype=float)
    if spots.size == 0 or taus.size == 0:
        raise TaskInputError("spots and taus are required")
    steps = int(payload.get("steps", 50))
    strike = float(payload.get("strike", 55.0))
    rate = float(payload.get("rate", 0.03))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.3))
    option_type = payload.get("option_type", "put").lower()
    exercise = payload.get("exercise", "american").lower()
    tree = payload.get("tree", "CRR")

    surface = []
    for s in spots:
        row = []
        for t in taus:
            res = price(
                {
                    "steps": steps,
                    "spot": float(s),
                    "strike": strike,
                    "rate": rate,
                    "vol": vol,
                    "tau": float(t),
                    "div_yield": div_yield,
                    "option_type": option_type,
                    "exercise": exercise,
                    "tree": tree,
                }
            )
            row.append(float(res["price"]))
        surface.append(row)

    return {
        "spots": [float(v) for v in spots],
        "taus": [float(v) for v in taus],
        "prices": surface,
        "artifacts": [],
        "warnings": [],
    }

