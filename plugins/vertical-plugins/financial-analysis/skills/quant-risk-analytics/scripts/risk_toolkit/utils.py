"""General utilities for quantitative risk analytics."""

from __future__ import annotations

from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd

from .errors import TaskInputError

def records_to_df(records: Any) -> pd.DataFrame:
    if isinstance(records, pd.DataFrame):
        return records.copy()
    if not isinstance(records, dict):
        raise TaskInputError("Expected a DataFrame or records dict")
    data = records.get("data")
    columns = records.get("columns")
    index = records.get("index")
    if data is None or columns is None:
        raise TaskInputError("Records must include 'data' and 'columns'")
    return pd.DataFrame(data=data, columns=columns, index=index)


def df_to_records(df: pd.DataFrame, *, stringify_index: bool = True) -> Dict[str, Any]:
    if stringify_index:
        index = [str(i) for i in df.index]
    else:
        index = df.index.tolist()
    return {
        "index": index,
        "columns": df.columns.tolist(),
        "data": df.to_numpy().tolist(),
    }


def require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise TaskInputError(f"Missing columns: {missing}")


def as_array(data: Any, *, name: str = "data", allow_empty: bool = False) -> np.ndarray:
    if data is None:
        raise TaskInputError(f"Missing {name}")
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.size == 0 and not allow_empty:
        raise TaskInputError(f"{name} must be non-empty")
    return arr


def ensure_positive(value: float, name: str) -> None:
    if value <= 0:
        raise TaskInputError(f"{name} must be positive")
