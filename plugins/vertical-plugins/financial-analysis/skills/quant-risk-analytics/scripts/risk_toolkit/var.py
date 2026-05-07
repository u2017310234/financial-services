"""Value-at-Risk utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional
import math

import numpy as np
import pandas as pd

from .errors import TaskInputError
from .data import fetch_prices
from .utils import records_to_df


def discrete_var(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    payouts = np.asarray(payload.get("payouts", []), dtype=float)
    probs = np.asarray(payload.get("probabilities", []), dtype=float)
    confidence = float(payload.get("confidence", 0.97))
    if payouts.size == 0 or probs.size == 0 or payouts.size != probs.size:
        raise TaskInputError("payouts and probabilities must be non-empty and equal length")
    if not 0.0 < confidence < 1.0:
        raise TaskInputError("confidence must be between 0 and 1")

    order = np.argsort(payouts)
    payouts_sorted = payouts[order]
    probs_sorted = probs[order]
    cumulative = np.cumsum(probs_sorted)
    idx = np.searchsorted(cumulative, 1.0 - confidence, side="right")
    idx = min(idx, payouts_sorted.size - 1)
    var_value = -float(payouts_sorted[idx])

    return {
        "var": var_value,
        "sorted": {"payouts": payouts_sorted.tolist(), "probabilities": probs_sorted.tolist()},
        "artifacts": [],
        "warnings": [],
    }


def portfolio_var_normal(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    confidence = float(payload.get("confidence", 0.99))
    holding_period = int(payload.get("holding_period", 1))
    initial_investment = float(payload.get("initial_investment", 1_000_000))
    weights = np.asarray(payload.get("weights", []), dtype=float)

    if not 0.0 < confidence < 1.0:
        raise TaskInputError("confidence must be between 0 and 1")
    if holding_period <= 0:
        raise TaskInputError("holding_period must be positive")

    if "prices" in payload:
        prices = records_to_df(payload["prices"])
    elif payload.get("local_path") or payload.get("tickers"):
        result = fetch_prices(payload, {"return_dataframe": True})
        prices = result["prices_df"]
    else:
        raise TaskInputError("Provide prices data or fetch parameters")

    log_returns = np.log(prices / prices.shift(1)).dropna()
    if weights.size == 0:
        weights = np.repeat(1.0 / log_returns.shape[1], log_returns.shape[1])
    if weights.size != log_returns.shape[1]:
        raise TaskInputError("weights size must match number of assets")

    mean_returns = log_returns.mean().to_numpy()
    cov = log_returns.cov().to_numpy()
    port_mean = float(weights.dot(mean_returns))
    port_vol = float(np.sqrt(weights.T.dot(cov).dot(weights)))

    try:
        from scipy.stats import norm
    except Exception as exc:
        raise TaskInputError(f"scipy is required for VaR: {exc}") from exc

    z = abs(norm.ppf(1.0 - confidence))
    var_norm = initial_investment * (port_vol * z - port_mean) * math.sqrt(holding_period)
    var_lognorm = initial_investment * (1.0 - math.exp(port_mean - port_vol * z)) * math.sqrt(holding_period)

    return {
        "portfolio_mean": port_mean,
        "portfolio_vol": port_vol,
        "var_normal": float(var_norm),
        "var_lognormal": float(var_lognorm),
        "artifacts": [],
        "warnings": [],
    }


def historical_parametric(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    confidence_levels = payload.get("confidence_levels", [0.9, 0.95, 0.99])

    if "returns" in payload:
        returns = np.asarray(payload["returns"], dtype=float).reshape(-1)
    elif "prices" in payload:
        prices = records_to_df(payload["prices"]).iloc[:, 0]
        returns = np.log(prices / prices.shift(1)).dropna().to_numpy()
    elif payload.get("local_path") or payload.get("tickers"):
        result = fetch_prices(payload, {"return_dataframe": True})
        prices = result["prices_df"].iloc[:, 0]
        returns = np.log(prices / prices.shift(1)).dropna().to_numpy()
    else:
        raise TaskInputError("Provide returns or prices input")

    mu = float(np.mean(returns))
    sigma = float(np.std(returns, ddof=1))

    try:
        from scipy.stats import norm
    except Exception as exc:
        raise TaskInputError(f"scipy is required for parametric VaR: {exc}") from exc

    historical = []
    parametric = []
    for level in confidence_levels:
        level = float(level)
        hist = float(np.quantile(returns, 1.0 - level))
        para = float(norm.ppf(1.0 - level, mu, sigma))
        historical.append({"confidence": level, "var": hist})
        parametric.append({"confidence": level, "var": para})

    return {
        "mean": mu,
        "std": sigma,
        "historical": historical,
        "parametric": parametric,
        "artifacts": [],
        "warnings": [],
    }


def mc_var(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    expected_return = float(payload.get("expected_return", 0.0))
    sigma = float(payload.get("sigma", 0.0))
    time_step = int(payload.get("time_step", 1440))
    trials = int(payload.get("trials", 500))
    confidence = float(payload.get("confidence", 0.95))
    initial_investment = float(payload.get("initial_investment", 1_000_000))
    seed = payload.get("seed")

    if time_step <= 0 or trials <= 0:
        raise TaskInputError("time_step and trials must be positive")
    if seed is not None:
        np.random.seed(int(seed))

    daily_returns = np.random.normal(expected_return / time_step, sigma / np.sqrt(time_step), time_step)
    var_value = initial_investment * np.percentile(daily_returns, (1.0 - confidence) * 100.0)

    return {
        "var": float(var_value),
        "mean_return": float(np.mean(daily_returns)),
        "std_return": float(np.std(daily_returns, ddof=1)),
        "artifacts": [],
        "warnings": [],
    }
