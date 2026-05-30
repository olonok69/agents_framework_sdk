# Analysis & Strategy Catalog (UI Combo)

This catalog defines the **authoritative classification** for every item exposed in the Django combo selector.
It is intended for:
- UI consistency (labels/icons)
- Agent behavior constraints
- Guardrail checks and validation

Legend:
- `Analysis`: research, screening, synthesis, or signal interpretation (not a pure trading-system backtest)
- `Strategy`: explicit rule-based trading system evaluation / backtest-style output

## Classification Table

| UI Action | Endpoint | Type | Notes |
|---|---|---|---|
| technical | `/technical` | Analysis | Comprehensive technical synthesis |
| scanner | `/scanner` | Analysis | Multi-symbol scan/ranking |
| fundamental | `/fundamental` | Analysis | Financial statement analysis |
| multisector | `/multisector` | Analysis | Sector comparison synthesis |
| combined | `/combined` | Analysis | Technical + fundamental synthesis |
| overnight_gaps | `/overnight_gaps` | Analysis | Gap behavior analysis, not a portfolio strategy engine |
| earnings_momentum | `/earnings_momentum` | Analysis | Earnings/volume momentum analysis/scanner |
| bollinger_breakout | `/bollinger_breakout` | Strategy | Rule-based trading strategy |
| gap_fade | `/gap_fade` | Strategy | Rule-based trading strategy |
| multi_timeframe | `/multi_timeframe` | Strategy | Rule-based trading strategy |
| pairs_trading | `/pairs_trading` | Strategy | Rule-based trading strategy |
| statistical_arbitrage | `/statistical_arbitrage` | Strategy | Rule-based trading strategy |
| vix_term_structure | `/vix_term_structure` | Strategy | Rule-based trading strategy |
| volatility_regime | `/volatility_regime` | Strategy | Rule-based trading strategy |
| bollinger_zscore_rsi | `/bollinger_zscore_rsi` | Strategy | Rule-based trading strategy |
| bollinger_fibonacci | `/bollinger_fibonacci` | Strategy | Rule-based trading strategy |
| macd_donchian | `/macd_donchian` | Strategy | Rule-based trading strategy |
| dual_moving_average | `/dual_moving_average` | Strategy | Rule-based trading strategy |

## UI Rules

- Use icon `🔎` for all **Analysis** items.
- Use icon `🧪` for all **Strategy** items.
- Keep explicit suffixes in selector labels:
  - `(Analysis)`
  - `(Strategy)`

## Agent/Guardrail Rules (for future enforcement)

### For Analysis items
- Must not present themselves as complete backtest engines unless explicit backtest metrics are provided by MCP output.
- Should focus on interpretation, synthesis, ranking, and signal context.
- If metrics are present, quote them exactly; do not fabricate missing values.

### For Strategy items
- Must include strategy-rule context and performance interpretation.
- Must use tool-grounded metrics (returns, drawdown, Sharpe, trades, win-rate when available).
- Must not claim data-access limitations when MCP already returned valid metrics.

## Related docs

- [bollinger_zscore_rsi_strategy.md](bollinger_zscore_rsi_strategy.md)
- [bollinger_fibonacci_strategy.md](bollinger_fibonacci_strategy.md)
- [macd_donchian_strategy.md](macd_donchian_strategy.md)
- [dual_moving_average_strategy.md](dual_moving_average_strategy.md)
- [overnight_gaps_strategy.md](overnight_gaps_strategy.md)
- [earnings_momentum_strategy.md](earnings_momentum_strategy.md)
