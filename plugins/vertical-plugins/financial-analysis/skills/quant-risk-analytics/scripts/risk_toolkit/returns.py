"""Return utilities (log/simple returns, covariance, correlation)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from .errors import TaskInputError
from .utils import df_to_records, records_to_df
from .data import fetch_prices


def _coerce_prices(payload: Dict[str, Any]) -> pd.DataFrame:
    if "prices_df" in payload and isinstance(payload["prices_df"], pd.DataFrame):
        return payload["prices_df"].copy()
    if "prices" in payload:
        return records_to_df(payload["prices"])
    if payload.get("local_path") or payload.get("tickers") or payload.get("source"):
        result = fetch_prices(payload, {"return_dataframe": True})
        return result["prices_df"]
    raise TaskInputError("Missing prices input")


def compute_returns(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    returns_type = payload.get("returns_type", "log").lower()
    freq = payload.get("freq")
    resample_method = payload.get("resample_method", "ffill")
    cumulative = bool(payload.get("cumulative", False))
    dropna = bool(payload.get("dropna", True))

    prices = _coerce_prices(payload)
    if freq:
        if resample_method == "last":
            prices = prices.resample(freq).last()
        else:
            prices = prices.resample(freq).ffill()

    if returns_type == "log":
        returns = np.log(prices / prices.shift(1))
    elif returns_type == "simple":
        returns = prices.pct_change()
    else:
        raise TaskInputError(f"Unsupported returns_type: {returns_type}")

    if dropna:
        returns = returns.dropna()

    result = {
        "returns": df_to_records(returns),
        "artifacts": [],
        "warnings": [],
    }
    if cumulative:
        cum = (returns + 1.0).cumprod()
        result["cumulative"] = df_to_records(cum)
    if options.get("return_dataframe"):
        result["returns_df"] = returns
    return result


def basic_stats(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    annualization_factor = float(payload.get("annualization_factor", 252))
    payload = dict(payload)
    payload.setdefault("returns_type", "log")
    returns_result = compute_returns(payload, {"return_dataframe": True})
    returns = returns_result["returns_df"]

    vol = returns.std() * np.sqrt(annualization_factor)
    cov = returns.cov()
    corr = returns.corr()

    result = {
        "returns": df_to_records(returns),
        "volatility": vol.to_dict(),
        "covariance": df_to_records(cov),
        "correlation": df_to_records(corr),
        "artifacts": [],
        "warnings": [],
    }
    if options.get("return_dataframe"):
        result["returns_df"] = returns
        result["cov_df"] = cov
        result["corr_df"] = corr
    return result
