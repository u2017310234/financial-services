"""Data access helpers (CSV/XLSX and remote price fetch)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .errors import TaskInputError
from .utils import df_to_records, records_to_df


def _load_csv(path: Path, date_col: Optional[str]) -> pd.DataFrame:
    if date_col:
        df = pd.read_csv(path, parse_dates=[date_col])
        df = df.set_index(date_col)
        return df
    df = pd.read_csv(path)
    if df.columns.size > 0 and "date" in [c.lower() for c in df.columns]:
        for col in df.columns:
            if col.lower() == "date":
                df[col] = pd.to_datetime(df[col])
                df = df.set_index(col)
                break
    return df


def _load_excel(path: Path, sheet_name: Optional[str], date_col: Optional[str]) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    return df


def load_dataset(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    local_path = payload.get("local_path")
    date_col = payload.get("date_col")
    sheet_name = payload.get("sheet_name")

    if not local_path:
        raise TaskInputError("local_path is required (this skill does not bundle datasets)")

    path = Path(local_path)

    if not path.exists():
        raise TaskInputError(f"Dataset not found: {path}")

    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        df = _load_excel(path, sheet_name, date_col)
    else:
        df = _load_csv(path, date_col)

    result = {
        "data": df_to_records(df),
        "summary": {
            "rows": int(df.shape[0]),
            "columns": df.columns.tolist(),
            "path": str(path),
        },
        "artifacts": [],
        "warnings": [],
    }
    if options.get("return_dataframe"):
        result["data_df"] = df
    return result


def fetch_prices(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    source = payload.get("source", "yahoo").lower()
    local_path = payload.get("local_path")
    date_col = payload.get("date_col", "Date")
    price_field = payload.get("price_field", "Adj Close")

    df = None
    if local_path:
        path = Path(local_path)
        if not path.exists():
            raise TaskInputError(f"local_path not found: {local_path}")
        df = _load_csv(path, date_col)
    elif source in ("yahoo", "fred"):
        tickers = payload.get("tickers")
        start = payload.get("start")
        end = payload.get("end")
        if not tickers or not start or not end:
            raise TaskInputError("tickers, start, end are required for remote sources")
        try:
            from pandas_datareader import data as pdr
        except Exception as exc:
            raise TaskInputError(f"pandas_datareader not available: {exc}") from exc
        data = pdr.DataReader(tickers, source, start, end)
        df = data[price_field] if source == "yahoo" else data
    else:
        raise TaskInputError(f"Unsupported source: {source}")

    result = {
        "prices": df_to_records(df),
        "summary": {"rows": int(df.shape[0]), "columns": df.columns.tolist()},
        "artifacts": [],
        "warnings": [],
    }
    if options.get("return_dataframe"):
        result["prices_df"] = df
    return result


def _coerce_prices(payload: Dict[str, Any]) -> pd.DataFrame:
    if "prices_df" in payload and isinstance(payload["prices_df"], pd.DataFrame):
        return payload["prices_df"].copy()
    if "prices" in payload:
        return records_to_df(payload["prices"])
    if payload.get("local_path") or payload.get("tickers") or payload.get("source"):
        result = fetch_prices(payload, {"return_dataframe": True})
        return result["prices_df"]
    raise TaskInputError("Missing prices input")


def price_mean(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    prices = _coerce_prices(payload)
    mean = prices.mean().to_dict()
    return {"mean": mean, "artifacts": [], "warnings": []}


def price_period_means(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    prices = _coerce_prices(payload)
    freq = payload.get("freq", "Q")
    start = payload.get("start")
    end = payload.get("end")

    if not isinstance(prices.index, pd.DatetimeIndex):
        try:
            prices.index = pd.to_datetime(prices.index)
        except Exception as exc:
            raise TaskInputError(f"prices index must be datetime: {exc}") from exc

    if isinstance(freq, str) and freq.upper() == "Q":
        freq = "QE"
    if start or end:
        prices = prices.loc[start:end]

    means = prices.resample(freq).mean()
    return {
        "means": df_to_records(means),
        "summary": {
            "periods": int(means.shape[0]),
            "columns": means.columns.tolist(),
            "freq": freq,
        },
        "artifacts": [],
        "warnings": [],
    }
