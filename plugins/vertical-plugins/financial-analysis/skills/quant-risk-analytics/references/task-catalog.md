# Task catalog

This catalog is generated from the skill's `tool_specs.json` and summarizes the available tasks.

## binomial

- `binomial.convergence_vs_bsm`: binomial price convergence versus Black-Scholes. (handler: `convergence_vs_bsm`; inputs: spot, strike, tau, rate, vol, div_yield, option_type, steps)
- `binomial.price`: binomial tree option price with optional tree output. (handler: `price`; inputs: spot, strike, tau, rate, vol, div_yield, exercise, option_type)
- `binomial.price_surface`: binomial price surface over spots and maturities. (handler: `price_surface`; inputs: strike, rate, vol, div_yield, exercise, option_type, spots, steps)
- `binomial.terminal_distribution`: terminal price distribution from binomial tree. (handler: `terminal_distribution`; inputs: spot, tau, rate, vol, div_yield, steps, tree)

## data

- `data.fetch_prices`: load prices from CSV or remote source (Yahoo/FRED). (handler: `fetch_prices`; inputs: local_path, date_col, end, price_field, source, start, tickers)
- `data.load_dataset`: load a named dataset or local file into records (requires local_path; no datasets bundled). (handler: `load_dataset`; inputs: local_path, date_col, name, sheet_name)
- `data.price_mean`: mean price per column. (handler: `price_mean`; inputs: local_path, prices, date_col, end, price_field, source, start, tickers)
- `data.price_period_means`: mean prices by resampled period. (handler: `price_period_means`; inputs: local_path, prices, date_col, end, freq, price_field, source, start)

## greeks

- `greeks.delta_surface`: delta surface over spot and maturity grid. (handler: `delta_surface`; inputs: strike, rate, vol, div_yield, spot_max, spot_min, spot_num, tau_max)
- `greeks.gamma_surface`: gamma surface over spot and maturity grid. (handler: `gamma_surface`; inputs: strike, rate, vol, div_yield, spot_max, spot_min, spot_num, tau_max)
- `greeks.rho_surface`: rho surface over spot and maturity grid. (handler: `rho_surface`; inputs: strike, rate, vol, div_yield, spot_max, spot_min, spot_num, tau_max)
- `greeks.theta_surface`: theta surface over spot and maturity grid. (handler: `theta_surface`; inputs: strike, rate, vol, div_yield, spot_max, spot_min, spot_num, tau_max)
- `greeks.vega_surface`: vega surface over spot and maturity grid. (handler: `vega_surface`; inputs: strike, rate, vol, div_yield, spot_max, spot_min, spot_num, tau_max)

## options

- `options.asset_or_nothing`: asset-or-nothing binary option price. (handler: `asset_or_nothing`; inputs: spot, strike, tau, rate, vol, div_yield, option_type)
- `options.binary_cash_or_nothing`: cash-or-nothing binary option price. (handler: `binary_cash_or_nothing`; inputs: spot, strike, tau, rate, vol, div_yield, option_type, payout)
- `options.binary_cash_or_nothing_delta`: delta of cash-or-nothing binary option. (handler: `binary_cash_or_nothing_delta`; inputs: spot, strike, tau, rate, vol, div_yield, option_type, payout)
- `options.binary_replication`: binary option replication using call spreads. (handler: `binary_replication`; inputs: strike, tau, rate, vol, div_yield, epsilons, payout, spots)
- `options.binary_replication_delta`: binary replication delta curve. (handler: `binary_replication_delta`; inputs: strike, tau, rate, vol, div_yield, epsilon, option_type, payout)
- `options.bsm_price`: black-Scholes price for European call and put. (handler: `bsm_price`; inputs: spot, strike, tau, rate, vol, div_yield)
- `options.bsm_price_curve`: option price curve by varying one parameter. (handler: `bsm_price_curve`; inputs: spot, strike, tau, rate, vol, div_yield, values, vary)
- `options.bsm_price_surface`: option price surface over spots and maturities. (handler: `bsm_price_surface`; inputs: strike, rate, vol, div_yield, spots, taus)
- `options.fx_option_price`: fX option price under Black-Scholes. (handler: `fx_option_price`; inputs: spot, strike, tau, vol, option_type, rate_domestic, rate_foreign)
- `options.implied_vol_bisection`: implied volatility via bisection. (handler: `implied_vol_bisection`; inputs: spot, strike, tau, rate, div_yield, max_iter, option_type, precision)
- `options.implied_vol_smile`: implied volatility smile from option dataset (requires local_path; no datasets bundled). (handler: `implied_vol_smile`; inputs: local_path, rate, method, dataset, date)
- `options.payoff_pnl`: payoff and PnL curves for vanilla options. (handler: `payoff_pnl`; inputs: strike, num, option_type, position, premium, spot_max, spot_min)

## portfolio

- `portfolio.capm_beta`: cAPM beta and systematic risk decomposition (requires local_path or provided data; no datasets bundled). (handler: `capm_beta`; inputs: local_path, data, dataset)
- `portfolio.efficient_frontier`: efficient frontier from portfolio statistics (requires local_path or provided data; no datasets bundled). (handler: `efficient_frontier`; inputs: local_path, allow_short, data, dataset, num, rp_max, rp_min)
- `portfolio.gmvp_analytic`: analytic global minimum variance portfolio (requires local_path or provided data; no datasets bundled). (handler: `gmvp_analytic`; inputs: local_path, covariance, data, dataset, mean_returns)
- `portfolio.portfolio_stats`: portfolio mean/vol/covariance/correlation statistics (requires local_path or provided data; no datasets bundled). (handler: `portfolio_stats`; inputs: local_path, data, dataset)
- `portfolio.two_asset_frontier`: two-asset efficient frontiers across correlations (requires local_path or provided data; no datasets bundled). (handler: `two_asset_frontier`; inputs: r1, r2, rho_range, vol1, vol2, w_max, w_min, w_num)

## returns

- `returns.basic_stats`: compute returns plus volatility, covariance, and correlation. (handler: `basic_stats`; inputs: local_path, prices, annualization_factor, date_col, dropna, end, freq, price_field)
- `returns.compute_returns`: compute log or simple returns from price series. (handler: `compute_returns`; inputs: local_path, prices, cumulative, date_col, dropna, end, freq, price_field)

## var

- `var.discrete_var`: discrete VaR from payout distribution. (handler: `discrete_var`; inputs: confidence, payouts, probabilities)
- `var.historical_parametric`: historical and parametric VaR from returns. (handler: `historical_parametric`; inputs: local_path, prices, returns, confidence_levels, date_col, end, price_field, source)
- `var.mc_var`: monte Carlo VaR from normal return draws. (handler: `mc_var`; inputs: confidence, expected_return, initial_investment, seed, sigma, time_step, trials)
- `var.portfolio_var_normal`: portfolio VaR with normal/lognormal approximation. (handler: `portfolio_var_normal`; inputs: local_path, prices, weights, confidence, date_col, end, holding_period, initial_investment)

## volatility

- `volatility.arch_garch_fit`: fit ARCH/GARCH model and return parameters. (handler: `arch_garch_fit`; inputs: local_path, prices, returns, column, date_col, dropna, end, freq)
- `volatility.cumulative_volatility`: expanding window volatility series. (handler: `cumulative_volatility`; inputs: local_path, prices, returns, column, date_col, dropna, end, freq)
- `volatility.ewma_volatility`: eWMA volatility series from returns. (handler: `ewma_volatility`; inputs: local_path, prices, returns, alpha, column, date_col, dropna, end)
- `volatility.historical_volatility`: compute sample and annualized volatility. (handler: `historical_volatility`; inputs: local_path, prices, returns, annualization_factor, column, date_col, dropna, end)
- `volatility.moving_volatility`: rolling window volatility series. (handler: `moving_volatility`; inputs: local_path, prices, returns, column, date_col, dropna, end, freq)
- `volatility.volatility_forecast_comparison`: compare EWMA, ARCH, and GARCH volatility forecasts. (handler: `volatility_forecast_comparison`; inputs: local_path, prices, returns, arch_params, column, date_col, dropna, end)
