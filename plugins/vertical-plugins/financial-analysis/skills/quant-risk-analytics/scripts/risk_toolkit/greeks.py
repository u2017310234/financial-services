"""Greek surface calculations."""

from __future__ import annotations

from typing import Any, Dict, Optional
import math

import numpy as np

from .errors import TaskInputError


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    erf_vec = np.vectorize(math.erf)
    return 0.5 * (1.0 + erf_vec(x / math.sqrt(2.0)))


def _norm_pdf(x: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _grid(payload: Dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    spot_min = float(payload.get("spot_min", 20.0))
    spot_max = float(payload.get("spot_max", 80.0))
    tau_min = float(payload.get("tau_min", 0.1))
    tau_max = float(payload.get("tau_max", 1.0))
    spot_num = int(payload.get("spot_num", 30))
    tau_num = int(payload.get("tau_num", 30))

    if spot_max <= spot_min or tau_max <= tau_min:
        raise TaskInputError("Invalid spot or tau range")
    if spot_num <= 1 or tau_num <= 1:
        raise TaskInputError("spot_num and tau_num must be > 1")

    spots = np.linspace(spot_min, spot_max, spot_num)
    taus = np.linspace(tau_min, tau_max, tau_num)
    return spots, taus


def delta_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots, taus = _grid(payload)
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    s_grid, t_grid = np.meshgrid(spots, taus, indexing="ij")
    d1 = (np.log(s_grid / strike) + (rate - div_yield + 0.5 * vol**2) * t_grid) / (vol * np.sqrt(t_grid))
    call_delta = _norm_cdf(d1) * np.exp(-div_yield * t_grid)
    put_delta = call_delta - np.exp(-div_yield * t_grid)

    return {
        "spots": spots.tolist(),
        "taus": taus.tolist(),
        "call_delta": call_delta.tolist(),
        "put_delta": put_delta.tolist(),
        "artifacts": [],
        "warnings": [],
    }


def gamma_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots, taus = _grid(payload)
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    s_grid, t_grid = np.meshgrid(spots, taus, indexing="ij")
    d1 = (np.log(s_grid / strike) + (rate - div_yield + 0.5 * vol**2) * t_grid) / (vol * np.sqrt(t_grid))
    gamma = np.exp(-div_yield * t_grid) * _norm_pdf(d1) / (s_grid * vol * np.sqrt(t_grid))

    return {
        "spots": spots.tolist(),
        "taus": taus.tolist(),
        "gamma": gamma.tolist(),
        "artifacts": [],
        "warnings": [],
    }


def theta_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots, taus = _grid(payload)
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    s_grid, t_grid = np.meshgrid(spots, taus, indexing="ij")
    d1 = (np.log(s_grid / strike) + (rate - div_yield + 0.5 * vol**2) * t_grid) / (vol * np.sqrt(t_grid))
    d2 = d1 - vol * np.sqrt(t_grid)
    pdf = _norm_pdf(d1)

    call_theta = (
        -np.exp(-div_yield * t_grid) * s_grid * pdf * vol / (2.0 * np.sqrt(t_grid))
        - rate * strike * np.exp(-rate * t_grid) * _norm_cdf(d2)
        + div_yield * s_grid * np.exp(-div_yield * t_grid) * _norm_cdf(d1)
    )
    put_theta = (
        -np.exp(-div_yield * t_grid) * s_grid * pdf * vol / (2.0 * np.sqrt(t_grid))
        + rate * strike * np.exp(-rate * t_grid) * _norm_cdf(-d2)
        - div_yield * s_grid * np.exp(-div_yield * t_grid) * _norm_cdf(-d1)
    )

    return {
        "spots": spots.tolist(),
        "taus": taus.tolist(),
        "call_theta": call_theta.tolist(),
        "put_theta": put_theta.tolist(),
        "artifacts": [],
        "warnings": [],
    }


def vega_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots, taus = _grid(payload)
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    s_grid, t_grid = np.meshgrid(spots, taus, indexing="ij")
    d1 = (np.log(s_grid / strike) + (rate - div_yield + 0.5 * vol**2) * t_grid) / (vol * np.sqrt(t_grid))
    vega = s_grid * np.exp(-div_yield * t_grid) * _norm_pdf(d1) * np.sqrt(t_grid)

    return {
        "spots": spots.tolist(),
        "taus": taus.tolist(),
        "vega": vega.tolist(),
        "artifacts": [],
        "warnings": [],
    }


def rho_surface(payload: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ = options
    spots, taus = _grid(payload)
    strike = float(payload.get("strike", 50.0))
    rate = float(payload.get("rate", 0.03))
    vol = float(payload.get("vol", 0.5))
    div_yield = float(payload.get("div_yield", 0.0))

    s_grid, t_grid = np.meshgrid(spots, taus, indexing="ij")
    d1 = (np.log(s_grid / strike) + (rate - div_yield + 0.5 * vol**2) * t_grid) / (vol * np.sqrt(t_grid))
    d2 = d1 - vol * np.sqrt(t_grid)

    call_rho = strike * t_grid * np.exp(-rate * t_grid) * _norm_cdf(d2)
    put_rho = -strike * t_grid * np.exp(-rate * t_grid) * _norm_cdf(-d2)

    return {
        "spots": spots.tolist(),
        "taus": taus.tolist(),
        "call_rho": call_rho.tolist(),
        "put_rho": put_rho.tolist(),
        "artifacts": [],
        "warnings": [],
    }

