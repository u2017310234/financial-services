"""Volatility estimation utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from .errors import TaskInputError
from .utils import df_to_records, records_to_df
from .returns import compute_returns


def _coerce_returns(payload: Dict[str, Any]) -> pd.Series:
    if "returns_df" in payload and isinstance(payload["returns_df"], pd.DataFrame):
        df = payload["returns_df"].copy()
    elif "returns" in payload:
        data = payload["returns"]
        if isinstance(data, dict):
            df = records_to_df(data)
        else:
            arr = np.asarray(data, dtype=float).reshape(-1)
            df = pd.DataFrame({"returns": arr})
    elif "prices" in payload or payload.get("tickers") or payload.get("local_path"):
        result = compute_returns(payload, {"return_dataframe": True})
        df = result["returns_df"]
    else:
        raise TaskInputError("Missing returns or prices input")

    column = payload.get("column")
    if column:
        if column not in df.columns:
            raise TaskInputError(f"Column not found in returns: {column}")
        series = df[column]
    else:
        series = df.iloc[:, 0]
    return series.dropna()


def historical_volatility(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    annualization_factor = float(payload.get("annualization_factor", 252))
    returns = _coerce_returns(payload)
    daily_std = float(np.std(returns, ddof=1))
    annualized = daily_std * np.sqrt(annualization_factor)
    return {
        "daily_volatility": daily_std,
        "annualized_volatility": float(annualized),
        "returns": [float(v) for v in returns.to_numpy()],
        "artifacts": [],
        "warnings": [],
    }


def moving_volatility(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    returns = _coerce_returns(payload)
    windows = payload.get("windows", [5, 50, 100, 250])
    dropna = bool(payload.get("dropna", True))
    result = {"windows": [], "artifacts": [], "warnings": []}
    for win in windows:
        win = int(win)
        if win <= 1:
            raise TaskInputError("windows must be > 1")
        series = returns.rolling(win).std()
        if dropna:
            series = series.dropna()
        result["windows"].append(
            {"window": win, "values": [float(v) for v in series.to_numpy()]}
        )
    return result


def cumulative_volatility(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    returns = _coerce_returns(payload)
    series = returns.expanding(1).std().dropna()
    return {
        "values": [float(v) for v in series.to_numpy()],
        "artifacts": [],
        "warnings": [],
    }


def ewma_volatility(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    returns = _coerce_returns(payload)
    lamb = payload.get("lambda")
    if lamb is None:
        alpha = float(payload.get("alpha", 0.06))
    else:
        lamb = float(lamb)
        if not 0.0 < lamb < 1.0:
            raise TaskInputError("lambda must be between 0 and 1")
        alpha = 1.0 - lamb
    series = returns.ewm(alpha=alpha, adjust=False).std().dropna()
    return {
        "alpha": float(alpha),
        "values": [float(v) for v in series.to_numpy()],
        "artifacts": [],
        "warnings": [],
    }


def arch_garch_fit(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    returns = _coerce_returns(payload)
    model = payload.get("model", "GARCH").upper()
    p = int(payload.get("p", 1))
    q = int(payload.get("q", 1))

    try:
        from arch import arch_model
    except Exception as exc:
        raise TaskInputError(f"arch is required for volatility fit: {exc}") from exc

    if model not in ("ARCH", "GARCH"):
        raise TaskInputError("model must be ARCH or GARCH")

    vol = "ARCH" if model == "ARCH" else "GARCH"
    am = arch_model(returns, mean="Constant", lags=0, vol=vol, p=p, o=0, q=q, dist="normal")
    res = am.fit(disp="off")
    return {
        "model": model,
        "params": {k: float(v) for k, v in res.params.items()},
        "conditional_volatility": [float(v) for v in res.conditional_volatility],
        "artifacts": [],
        "warnings": [],
    }


def volatility_forecast_comparison(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    returns = _coerce_returns(payload)
    lookback = int(payload.get("lookback", 250))
    if lookback <= 1 or lookback > len(returns):
        raise TaskInputError("lookback must be between 2 and length of returns")
    r = returns.iloc[-lookback:]

    lamb = float(payload.get("lambda", 0.94))
    if not 0.0 < lamb < 1.0:
        raise TaskInputError("lambda must be between 0 and 1")
    vol_ewma = np.zeros(lookback)
    vol_ewma[0] = float(returns.iloc[-lookback: -lookback + 5].std())
    for i in range(lookback - 1):
        vol_ewma[i + 1] = np.sqrt(lamb * vol_ewma[i] ** 2 + (1.0 - lamb) * r.iloc[i] ** 2)

    arch_params = payload.get("arch_params", {"omega": 0.000068, "alpha1": 0.45})
    omega_arch = float(arch_params.get("omega", 0.000068))
    alpha1 = float(arch_params.get("alpha1", 0.45))
    vol_arch = np.zeros(lookback)
    vol_arch[0] = np.sqrt(omega_arch + alpha1 * returns.iloc[-lookback - 1] ** 2)
    for i in range(lookback - 1):
        vol_arch[i + 1] = np.sqrt(omega_arch + alpha1 * r.iloc[i] ** 2)

    garch_params = payload.get("garch_params", {"omega": 0.000002, "alpha1": 0.2, "beta1": 0.78})
    omega = float(garch_params.get("omega", 0.000002))
    alpha_g = float(garch_params.get("alpha1", 0.2))
    beta_g = float(garch_params.get("beta1", 0.78))
    vol_garch = np.zeros(lookback)
    vol_garch[0] = float(returns.iloc[-lookback: -lookback + 5].std())
    for i in range(lookback - 1):
        vol_garch[i + 1] = np.sqrt(omega + alpha_g * r.iloc[i] ** 2 + beta_g * vol_garch[i] ** 2)

    return {
        "ewma": [float(v) for v in vol_ewma],
        "arch": [float(v) for v in vol_arch],
        "garch": [float(v) for v in vol_garch],
        "artifacts": [],
        "warnings": [],
    }

