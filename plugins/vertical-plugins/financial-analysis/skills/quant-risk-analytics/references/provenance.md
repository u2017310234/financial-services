# Provenance

## Code origin

This skill is derived from Python modules found in this workspace under:

- `C:\Users\Administrator\risk_practice_toolkit` (the packaged toolkit source files)

The code was reorganized into the Codex “skill” layout and trimmed to the `quant-risk-analytics` scope (returns, volatility, VaR, vanilla options, binomial tree pricing, Greeks, and basic portfolio analytics).

## Key modifications

- Removed references to prior “book” naming in module docstrings.
- Pruned `tool_specs.json` to keep only task prefixes relevant to this skill:
  - `data.*`, `returns.*`, `volatility.*`, `var.*`, `options.*`, `binomial.*`, `greeks.*`, `portfolio.*`
- Disabled “built-in dataset” loading: file-based tasks require user-provided `local_path` (no datasets are shipped with this skill).

## Data files

No third-party datasets are redistributed with this skill.
