"""Option pricing utilities (vanilla pricing, implied vol, payoffs)."""

from __future__ import annotations

from typing import Any, Dict, Optional
import math

import numpy as np
import pandas as pd

from .errors import TaskInputError
from .utils import df_to_records


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bsm_d1_d2(spot: float, strike: float, tau: float, rate: float, vol: float, div_yield: float) -> tuple[float, float]:
    d1 = (math.log(spot / strike) + (rate - div_yield + 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
    d2 = d1 - vol * math.sqrt(tau)
    return d1, d2


def bsm_price(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    try:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        tau = float(payload["tau"])
        rate = float(payload.get("rate", 0.0))
        vol = float(payload["vol"])
        div_yield = float(payload.get("div_yield", 0.0))
    except KeyError as exc:
        raise TaskInputError(f"Missing key: {exc}") from exc

    if spot <= 0 or strike <= 0 or tau <= 0 or vol <= 0:
        raise TaskInputError("spot, strike, tau, vol must be positive")

    d1, d2 = _bsm_d1_d2(spot, strike, tau, rate, vol, div_yield)
    call = spot * math.exp(-div_yield * tau) * _norm_cdf(d1) - strike * math.exp(-rate * tau) * _norm_cdf(d2)
    put = strike * math.exp(-rate * tau) * _norm_cdf(-d2) - spot * math.exp(-div_yield * tau) * _norm_cdf(-d1)
    return {
        "call": float(call),
        "put": float(put),
        "inputs": {
            "spot": spot,
            "strike": strike,
            "tau": tau,
            "rate": rate,
            "vol": vol,
            "div_yield": div_yield,
        },
        "artifacts": [],
        "warnings": [],
    }


def bsm_price_curve(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    vary = payload.get("vary", "strike")
    values = payload.get("values")
    if values is None:
        raise TaskInputError("values list is required")
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        raise TaskInputError("values must be non-empty")

    spot = float(payload.get("spot", 50.0))
    strike = float(payload.get("strike", 50.0))
    tau = float(payload.get("tau", 1.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    call = []
    put = []
    for v in values:
        params = {"spot": spot, "strike": strike, "tau": tau, "rate": rate, "vol": vol, "div_yield": div_yield}
        if vary == "strike":
            params["strike"] = float(v)
        elif vary == "spot":
            params["spot"] = float(v)
        elif vary == "tau":
            params["tau"] = float(v)
        else:
            raise TaskInputError("vary must be strike, spot, or tau")
        price = bsm_price(params)
        call.append(float(price["call"]))
        put.append(float(price["put"]))

    return {
        "vary": vary,
        "values": [float(v) for v in values],
        "call": call,
        "put": put,
        "artifacts": [],
        "warnings": [],
    }


def bsm_price_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots = np.asarray(payload.get("spots", []), dtype=float)
    taus = np.asarray(payload.get("taus", []), dtype=float)
    if spots.size == 0 or taus.size == 0:
        raise TaskInputError("spots and taus are required")
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    call = []
    put = []
    for s in spots:
        row_call = []
        row_put = []
        for t in taus:
            price = bsm_price(
                {
                    "spot": float(s),
                    "strike": strike,
                    "tau": float(t),
                    "rate": rate,
                    "vol": vol,
                    "div_yield": div_yield,
                }
            )
            row_call.append(float(price["call"]))
            row_put.append(float(price["put"]))
        call.append(row_call)
        put.append(row_put)

    return {
        "spots": [float(v) for v in spots],
        "taus": [float(v) for v in taus],
        "call": call,
        "put": put,
        "artifacts": [],
        "warnings": [],
    }


def fx_option_price(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    try:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        tau = float(payload["tau"])
        rate_domestic = float(payload["rate_domestic"])
        rate_foreign = float(payload["rate_foreign"])
        vol = float(payload["vol"])
        option_type = payload.get("option_type", "call").lower()
    except KeyError as exc:
        raise TaskInputError(f"Missing key: {exc}") from exc

    if spot <= 0 or strike <= 0 or tau <= 0 or vol <= 0:
        raise TaskInputError("spot, strike, tau, vol must be positive")
    d1 = (math.log(spot / strike) + (rate_domestic - rate_foreign + 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
    d2 = d1 - vol * math.sqrt(tau)
    if option_type == "call":
        price = spot * math.exp(-rate_foreign * tau) * _norm_cdf(d1) - strike * math.exp(-rate_domestic * tau) * _norm_cdf(d2)
    elif option_type == "put":
        price = strike * math.exp(-rate_domestic * tau) * _norm_cdf(-d2) - spot * math.exp(-rate_foreign * tau) * _norm_cdf(-d1)
    else:
        raise TaskInputError("option_type must be call or put")
    return {"price": float(price), "artifacts": [], "warnings": []}


def implied_vol_bisection(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    option_type = payload.get("option_type", "call").lower()
    price = float(payload.get("price", 0.0))
    spot = float(payload.get("spot", 0.0))
    strike = float(payload.get("strike", 0.0))
    rate = float(payload.get("rate", 0.0))
    tau = float(payload.get("tau", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    precision = float(payload.get("precision", 1e-5))
    max_iter = int(payload.get("max_iter", 100))
    low = float(payload.get("vol_low", 1e-6))
    high = float(payload.get("vol_high", 5.0))

    if spot <= 0 or strike <= 0 or tau <= 0 or price <= 0:
        raise TaskInputError("price, spot, strike, tau must be positive")
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        mid_price = bsm_price(
            {
                "spot": spot,
                "strike": strike,
                "tau": tau,
                "rate": rate,
                "vol": mid,
                "div_yield": div_yield,
            }
        )
        model_price = mid_price["call"] if option_type == "call" else mid_price["put"]
        if abs(model_price - price) < precision:
            return {"implied_vol": float(mid), "iterations": max_iter, "artifacts": [], "warnings": []}
        if model_price > price:
            high = mid
        else:
            low = mid

    return {"implied_vol": float(mid), "iterations": max_iter, "artifacts": [], "warnings": ["max_iter reached"]}


def implied_vol_smile(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    local_path = payload.get("local_path")
    date_value = payload.get("date")
    rate = float(payload.get("rate", 0.002))
    method = payload.get("method", "bisection").lower()

    if not local_path:
        raise TaskInputError("local_path is required (this skill does not bundle datasets)")
    path = local_path
    df = pd.read_csv(path)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    if date_value:
        date_value = pd.to_datetime(date_value)
        df = df[df["date"] == date_value]

    strikes = df["strike"].to_numpy()
    ivs = []
    warnings = []
    for _, row in df.iterrows():
        spot = float(row["underlying value"])
        strike = float(row["strike"])
        tau = float(row["days to maturity"]) / 365.0
        price = float(row["call price"])
        if method == "mibian":
            try:
                from mibian import BS
            except Exception as exc:
                raise TaskInputError(f"mibian not available: {exc}") from exc
            result = BS([spot, strike, rate, row["days to maturity"]], callPrice=price)
            iv = float(result.impliedVolatility)
        else:
            iv_result = implied_vol_bisection(
                {
                    "option_type": "call",
                    "price": price,
                    "spot": spot,
                    "strike": strike,
                    "rate": rate,
                    "tau": tau,
                    "div_yield": 0.0,
                }
            )
            iv = float(iv_result["implied_vol"])
            if iv_result.get("warnings"):
                warnings.extend(iv_result["warnings"])
        ivs.append(iv)

    return {
        "strike": [float(v) for v in strikes],
        "implied_vol": [float(v) for v in ivs],
        "date": str(date_value.date()) if date_value is not None else None,
        "artifacts": [],
        "warnings": warnings,
    }


def payoff_pnl(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    strike = float(payload.get("strike", 100.0))
    option_type = payload.get("option_type", "call").lower()
    position = payload.get("position", "long").lower()
    premium = float(payload.get("premium", 0.0))
    spot_min = float(payload.get("spot_min", 0.0))
    spot_max = float(payload.get("spot_max", 200.0))
    num = int(payload.get("num", 200))

    if spot_max <= spot_min or num <= 1:
        raise TaskInputError("Invalid spot range or num")
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")
    if position not in ("long", "short"):
        raise TaskInputError("position must be long or short")

    spots = np.linspace(spot_min, spot_max, num)
    if option_type == "call":
        payoff = np.maximum(spots - strike, 0.0)
    else:
        payoff = np.maximum(strike - spots, 0.0)
    if position == "short":
        payoff = -payoff
    pnl = payoff - (premium if position == "long" else -premium)

    return {
        "spot": [float(v) for v in spots],
        "payoff": [float(v) for v in payoff],
        "pnl": [float(v) for v in pnl],
        "artifacts": [],
        "warnings": [],
    }


def binary_cash_or_nothing(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spot = float(payload.get("spot", 0.0))
    strike = float(payload.get("strike", 0.0))
    tau = float(payload.get("tau", 0.0))
    rate = float(payload.get("rate", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.0))
    payout = float(payload.get("payout", 1.0))
    option_type = payload.get("option_type", "call").lower()
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")
    if tau < 0:
        raise TaskInputError("tau must be >= 0")
    if tau == 0:
        if option_type == "call":
            price = payout if spot >= strike else 0.0
        else:
            price = payout if spot <= strike else 0.0
    else:
        if spot <= 0 or strike <= 0 or vol <= 0:
            raise TaskInputError("spot, strike, vol must be positive")
        d2 = (math.log(spot / strike) + (rate - div_yield - 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
        if option_type == "call":
            price = payout * math.exp(-rate * tau) * _norm_cdf(d2)
        else:
            price = payout * math.exp(-rate * tau) * _norm_cdf(-d2)
    return {"price": float(price), "artifacts": [], "warnings": []}


def binary_cash_or_nothing_delta(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spot = float(payload.get("spot", 0.0))
    strike = float(payload.get("strike", 0.0))
    tau = float(payload.get("tau", 0.0))
    rate = float(payload.get("rate", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.0))
    payout = float(payload.get("payout", 1.0))
    option_type = payload.get("option_type", "call").lower()
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")
    if spot <= 0 or strike <= 0 or vol <= 0 or tau <= 0:
        raise TaskInputError("spot, strike, vol, tau must be positive")
    d2 = (math.log(spot / strike) + (rate - div_yield - 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
    sign = 1.0 if option_type == "call" else -1.0
    delta = sign * payout * math.exp(-rate * tau) * _norm_pdf(sign * d2) / (spot * vol * math.sqrt(tau))
    return {"delta": float(delta), "artifacts": [], "warnings": []}


def binary_replication(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots = np.asarray(payload.get("spots", []), dtype=float)
    if spots.size == 0:
        raise TaskInputError("spots is required")
    strike = float(payload.get("strike", 0.0))
    tau = float(payload.get("tau", 0.0))
    rate = float(payload.get("rate", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.0))
    payout = float(payload.get("payout", 1.0))
    epsilons = np.asarray(payload.get("epsilons", [0.01 * strike]), dtype=float)

    if strike <= 0 or tau < 0 or vol < 0:
        raise TaskInputError("strike, tau, vol must be non-negative, strike > 0")

    curves = []
    for eps in epsilons:
        eps = float(eps)
        if eps <= 0:
            raise TaskInputError("epsilons must be positive")
        n = 0.5 * payout / eps
        values = []
        for s in spots:
            if tau == 0:
                price = payout if s >= strike else 0.0
            else:
                c1 = bsm_price({"spot": s, "strike": strike - eps, "tau": tau, "rate": rate, "vol": vol, "div_yield": div_yield})
                c2 = bsm_price({"spot": s, "strike": strike + eps, "tau": tau, "rate": rate, "vol": vol, "div_yield": div_yield})
                price = n * (c1["call"] - c2["call"])
            values.append(float(price))
        curves.append({"epsilon": eps, "values": values})

    return {"spots": [float(v) for v in spots], "curves": curves, "artifacts": [], "warnings": []}


def binary_replication_delta(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots = np.asarray(payload.get("spots", []), dtype=float)
    if spots.size == 0:
        raise TaskInputError("spots is required")
    strike = float(payload.get("strike", 0.0))
    tau = float(payload.get("tau", 0.0))
    rate = float(payload.get("rate", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.0))
    payout = float(payload.get("payout", 1.0))
    epsilon = float(payload.get("epsilon", 0.05 * strike))
    option_type = payload.get("option_type", "call").lower()

    if epsilon <= 0 or strike <= 0:
        raise TaskInputError("epsilon and strike must be positive")
    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")

    n = 0.5 * payout / epsilon
    values = []
    for s in spots:
        d1 = (math.log(s / (strike - epsilon)) + (rate - div_yield + 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
        d2 = (math.log(s / (strike + epsilon)) + (rate - div_yield + 0.5 * vol**2) * tau) / (vol * math.sqrt(tau))
        if option_type == "call":
            delta = n * (math.exp(-div_yield * tau) * _norm_cdf(d1) - math.exp(-div_yield * tau) * _norm_cdf(d2))
        else:
            delta = n * (math.exp(-div_yield * tau) * (_norm_cdf(d1) - 1.0) - math.exp(-div_yield * tau) * (_norm_cdf(d2) - 1.0))
        values.append(float(delta))

    return {"spots": [float(v) for v in spots], "delta": values, "artifacts": [], "warnings": []}


def asset_or_nothing(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spot = float(payload.get("spot", 0.0))
    strike = float(payload.get("strike", 0.0))
    tau = float(payload.get("tau", 0.0))
    rate = float(payload.get("rate", 0.0))
    div_yield = float(payload.get("div_yield", 0.0))
    vol = float(payload.get("vol", 0.0))
    option_type = payload.get("option_type", "call").lower()

    if option_type not in ("call", "put"):
        raise TaskInputError("option_type must be call or put")
    if tau < 0:
        raise TaskInputError("tau must be >= 0")
    if tau == 0:
        if option_type == "call":
            price = spot if spot >= strike else 0.0
        else:
            price = spot if spot <= strike else 0.0
    else:
        if spot <= 0 or strike <= 0 or vol <= 0:
            raise TaskInputError("spot, strike, vol must be positive")
        d1, _ = _bsm_d1_d2(spot, strike, tau, rate, vol, div_yield)
        if option_type == "call":
            price = spot * math.exp(-div_yield * tau) * _norm_cdf(d1)
        else:
            price = spot * math.exp(-div_yield * tau) * _norm_cdf(-d1)
    return {"price": float(price), "artifacts": [], "warnings": []}
