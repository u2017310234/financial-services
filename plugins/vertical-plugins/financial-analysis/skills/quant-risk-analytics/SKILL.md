## quant-risk-analytics

Quantitative risk & derivatives analytics skill (deterministic calculations).

### Scope

Includes:
- returns / covariance / correlation
- volatility (historical, moving, EWMA, ARCH/GARCH if optional deps installed)
- VaR (historical, parametric, Monte Carlo)
- vanilla option pricing (BSM), implied vol, payoff/PnL helpers
- binomial tree pricing (CRR/JR/LR), convergence checks
- Greeks surfaces
- basic portfolio risk stats and simple frontiers

Excludes:
- credit scorecards / WOE / survival models
- counterparty CVA / exposure simulation
- generic regression demos

### How to use (Python)

The entrypoint is `risk_toolkit.api.run(task, payload, options=None)`.

Example:

```python
from risk_toolkit import api

api.run(
    "options.bsm_price",
    {"spot": 100, "strike": 100, "tau": 1, "rate": 0.03, "vol": 0.2, "div_yield": 0},
)
```

### Tasks

Tasks are loaded from `scripts/risk_toolkit/tool_specs.json` and are grouped by prefix:
- `data.*`
- `returns.*`
- `volatility.*`
- `var.*`
- `options.*`
- `binomial.*`
- `greeks.*`
- `portfolio.*`

See `references/task-catalog.md` for the full list.

### Data policy

This skill does not ship external datasets. For tasks that load data, pass `local_path` or provide `data` / `data_df` directly.

### Optional dependencies

Some tasks require extra packages:
- `arch` for `volatility.arch_garch_fit`
- `pandas_datareader` for remote price fetch in `data.fetch_prices`
- `qpsolvers` or `scipy` for constrained efficient frontier (`portfolio.efficient_frontier` with `allow_short=False`)
- `mibian` for `options.implied_vol_smile` when `method="mibian"`

### Disclaimer

For educational and analytical use only. Not investment advice.

