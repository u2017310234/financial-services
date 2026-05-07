"""Portfolio analytics utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional
import math

import numpy as np
import pandas as pd

from .errors import TaskInputError
from .data import load_dataset
from .utils import df_to_records, records_to_df


def _load_portfolio_data(payload: Dict[str, Any], dataset_name: str) -> pd.DataFrame:
    if "data_df" in payload and isinstance(payload["data_df"], pd.DataFrame):
        return payload["data_df"].copy()
    if "data" in payload:
        return records_to_df(payload["data"])
    if payload.get("local_path"):
        result = load_dataset({"local_path": payload.get("local_path")}, {"return_dataframe": True})
        return result["data_df"]
    raise TaskInputError("Provide portfolio data via 'data' / 'data_df' or 'local_path' (no datasets bundled)")


def portfolio_stats(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    df = _load_portfolio_data(payload, "data_portfolio_1")
    mean_returns = df.mean() * 12
    vol = df.std() * np.sqrt(12)
    cov = df.cov() * 12
    corr = df.corr()
    return {
        "mean_returns": mean_returns.to_dict(),
        "volatility": vol.to_dict(),
        "covariance": df_to_records(cov),
        "correlation": df_to_records(corr),
        "artifacts": [],
        "warnings": [],
    }


def two_asset_frontier(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    r1 = float(payload.get("r1", 0.11))
    r2 = float(payload.get("r2", 0.16))
    vol1 = float(payload.get("vol1", 0.25))
    vol2 = float(payload.get("vol2", 0.38))
    rho_range = payload.get("rho_range", [-1.0, -0.5, 0.0, 0.5, 1.0])
    weights = np.linspace(float(payload.get("w_min", -0.3)), float(payload.get("w_max", 1.5)), int(payload.get("w_num", 190)))

    results = []
    for rho in rho_range:
        rho = float(rho)
        port_return = weights * r1 + (1.0 - weights) * r2
        port_vol = np.sqrt((weights * vol1) ** 2 + ((1.0 - weights) * vol2) ** 2 + 2 * weights * (1.0 - weights) * vol1 * vol2 * rho)
        w1_star = (vol2**2 - rho * vol1 * vol2) / (vol1**2 - 2 * rho * vol1 * vol2 + vol2**2)
        w2_star = 1.0 - w1_star
        gmvp_return = w1_star * r1 + w2_star * r2
        gmvp_vol = math.sqrt((w1_star * vol1) ** 2 + (w2_star * vol2) ** 2 + 2 * w1_star * w2_star * vol1 * vol2 * rho)
        results.append(
            {
                "rho": rho,
                "weights": weights.tolist(),
                "returns": port_return.tolist(),
                "volatility": port_vol.tolist(),
                "gmvp": {"w1": float(w1_star), "w2": float(w2_star), "return": float(gmvp_return), "vol": float(gmvp_vol)},
            }
        )

    return {"frontiers": results, "artifacts": [], "warnings": []}


def gmvp_analytic(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    if "covariance" in payload:
        cov = records_to_df(payload["covariance"]).to_numpy(dtype=float)
        mean_returns = np.asarray(payload.get("mean_returns", []), dtype=float)
    else:
        stats = portfolio_stats(payload)
        cov = records_to_df(stats["covariance"]).to_numpy(dtype=float)
        mean_returns = np.asarray(list(stats["mean_returns"].values()), dtype=float)

    if cov.size == 0:
        raise TaskInputError("covariance matrix is required")

    inv_cov = np.linalg.inv(cov)
    ones = np.ones(cov.shape[0])
    weights = inv_cov.dot(ones) / (ones.T.dot(inv_cov).dot(ones))
    port_vol = float(np.sqrt(weights.T.dot(cov).dot(weights)))
    port_return = float(weights.dot(mean_returns)) if mean_returns.size else None

    return {
        "weights": weights.tolist(),
        "volatility": port_vol,
        "return": port_return,
        "artifacts": [],
        "warnings": [],
    }


def efficient_frontier(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    allow_short = bool(payload.get("allow_short", True))
    stats = portfolio_stats(payload)
    mean_returns = np.asarray(list(stats["mean_returns"].values()), dtype=float)
    cov = records_to_df(stats["covariance"]).to_numpy(dtype=float)
    if cov.size == 0:
        raise TaskInputError("covariance matrix is required")

    rp_min = float(payload.get("rp_min", float(np.min(mean_returns))))
    rp_max = float(payload.get("rp_max", float(np.max(mean_returns))))
    num = int(payload.get("num", 25))
    rp_range = np.linspace(rp_min, rp_max, num)

    if allow_short:
        inv_cov = np.linalg.inv(cov)
        ones = np.ones(cov.shape[0])
        a = ones.T.dot(inv_cov).dot(ones)
        b = ones.T.dot(inv_cov).dot(mean_returns)
        c = mean_returns.T.dot(inv_cov).dot(mean_returns)
        det = a * c - b * b
        vols = []
        for rp in rp_range:
            w = inv_cov.dot(((c - b * rp) / det) * ones + ((a * rp - b) / det) * mean_returns)
            vols.append(float(np.sqrt(w.T.dot(cov).dot(w))))
        return {"rp_range": rp_range.tolist(), "volatility": vols, "artifacts": [], "warnings": []}

    try:
        from qpsolvers import solve_qp
        solver = "qpsolvers"
    except Exception:
        try:
            from scipy.optimize import minimize, LinearConstraint, Bounds
            solver = "scipy"
        except Exception as exc:
            raise TaskInputError(f"qpsolvers or scipy required: {exc}") from exc

    vols = []
    n = mean_returns.size
    for rp in rp_range:
        if solver == "qpsolvers":
            w = solve_qp(
                cov,
                np.zeros_like(mean_returns),
                -np.identity(n),
                np.zeros_like(mean_returns),
                np.vstack([np.ones(n), mean_returns]),
                np.array([1.0, rp]),
            )
        else:
            def obj(w):
                return w.T.dot(cov).dot(w)

            cons = [LinearConstraint(np.ones(n), [1], [1]), LinearConstraint(mean_returns, [rp], [rp])]
            bounds = Bounds(np.zeros(n), np.ones(n))
            w0 = np.ones(n) / n
            res = minimize(obj, w0, method="trust-constr", constraints=cons, bounds=bounds)
            w = res.x
        vols.append(float(np.sqrt(w.T.dot(cov).dot(w))))

    return {"rp_range": rp_range.tolist(), "volatility": vols, "artifacts": [], "warnings": []}


def capm_beta(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    df = _load_portfolio_data(payload, "data_portfolio_2")
    if df.shape[1] < 3:
        raise TaskInputError("Data must include assets, market excess, and risk-free columns")

    asset_returns = df.iloc[:, 1:-2]
    mkt_excess = df.iloc[:, -2]
    rf = df.iloc[:, -1]
    excess = asset_returns.sub(rf, axis=0)

    corr = excess.corrwith(mkt_excess)
    vol_excess = excess.std() * np.sqrt(12)
    vol_mkt = float(mkt_excess.std() * np.sqrt(12))

    beta = corr * vol_excess / vol_mkt
    sys_vol = beta * vol_mkt
    sys_pct = (sys_vol**2) / (vol_excess**2)

    return {
        "beta": beta.to_dict(),
        "systematic_vol": sys_vol.to_dict(),
        "systematic_pct": sys_pct.to_dict(),
        "artifacts": [],
        "warnings": [],
    }
