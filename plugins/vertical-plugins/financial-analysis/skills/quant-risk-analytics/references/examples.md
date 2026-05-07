# Examples

These examples call the skill entrypoint `risk_toolkit.api.run(task, payload, options=None)`.

## Black–Scholes–Merton price (vanilla)

```python
from risk_toolkit import api

result = api.run(
    "options.bsm_price",
    {"spot": 100, "strike": 100, "tau": 1, "rate": 0.03, "vol": 0.2, "div_yield": 0},
)
```

Expected shape:
- `result["status"] == "ok"`
- `result["result"]` contains `call` and `put`

## Returns from a price series (inline records)

```python
from risk_toolkit import api

prices = {
    "index": ["2026-01-01", "2026-01-02", "2026-01-03"],
    "columns": ["PX"],
    "data": [[100.0], [101.0], [99.0]],
}

result = api.run("returns.compute_returns", {"prices": prices, "returns_type": "log"})
```

## Historical volatility from returns (inline list)

```python
from risk_toolkit import api

result = api.run(
    "volatility.historical_volatility",
    {"returns": [0.01, -0.02, 0.005, 0.012, -0.008], "annualization_factor": 252},
)
```

## Parametric VaR (normal approximation)

```python
from risk_toolkit import api

result = api.run(
    "var.parametric_var",
    {"returns": [0.01, -0.02, 0.005, 0.012, -0.008], "confidence": 0.95},
)
```

## Notes

- Tasks that read files require `local_path`. The skill does not bundle external datasets.
- For educational and analytical use only. Not investment advice.

