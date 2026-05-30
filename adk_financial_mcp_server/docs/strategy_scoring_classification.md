# Strategy Scoring Classification (MCP Server)

This document classifies MCP strategy/analysis tools by how they generate outcomes:

- **Score-driven:** Explicit numeric scoring model (typically composite score, weighted components, or normalized score ranges).
- **Rule-driven:** Threshold/event/regime logic and/or backtest simulation outputs without a single composite score model as the primary decision engine.
- **Hybrid:** Aggregates or orchestrates score-driven and rule-driven components.

## 1) Score-driven tools

| Module | Primary MCP tools | Why score-driven |
|---|---|---|
| `server/strategies/bollinger_fibonacci.py` | `calculate_bollinger_fibonacci_score`, `analyze_bollinger_fibonacci_performance` | Uses explicit `Strategy_Score` with weighted components (BB, volatility, Fibonacci interaction, momentum). |
| `server/strategies/macd_donchian.py` | `calculate_macd_score_tool`, `calculate_donchian_channel_score_tool`, `calculate_combined_score_macd_donchian`, `analyze_macd_donchian_performance` | MACD and Donchian each produce normalized scores; combined score averages both. |
| `server/strategies/connors_zscore.py` | `calculate_connors_rsi_score_tool`, `calculate_zscore_indicator_tool`, `calculate_combined_connors_zscore_tool`, `analyze_connors_zscore_performance` | Connors and Z-score indicators generate numeric scores, combined with weights. |
| `server/strategies/dual_moving_average.py` | `calculate_dual_ma_score`, `analyze_dual_ma_performance` | Multi-component score model (positioning, signal strength, momentum) merged into total score. |
| `server/strategies/bollinger_zscore.py` | `calculate_bollinger_z_score`, `analyze_bollinger_zscore_performance` | Uses z-score distance from rolling mean with score/signal interpretation. |

## 2) Rule-driven tools

| Module | Primary MCP tools | Why rule-driven |
|---|---|---|
| `server/strategies/bollinger_zscore_rsi.py` | `analyze_bollinger_zscore_rsi` | Entry/exit rules via thresholds (`zscore` + RSI), returns trades/signals/metrics. |
| `server/strategies/bollinger_breakout.py` | `analyze_bollinger_breakout` | Breakout/confirmation rules using band/ATR/volume conditions. |
| `server/strategies/gap_strategy.py` | `analyze_overnight_gaps` | Gap classification + fill-rate/event statistics, no composite score engine. |
| `server/strategies/earnings_momentum.py` | `analyze_earnings_momentum` | Volume-spike and hold-window simulation, signal/trade aggregation. |
| `server/strategies/trin_strategy.py` | `analyze_trin_market_breadth` | Band/regime signal derivation from TRIN behavior. |
| `server/strategies/gap_fade.py` | `analyze_gap_fade` | Gap threshold + intraday fade holding rules. |
| `server/strategies/multi_timeframe.py` | `analyze_multi_timeframe` | MA trend + RSI threshold state machine. |
| `server/strategies/pairs_trading.py` | `analyze_pairs_trading` | Spread z-score threshold entry/exit rules (rule-triggered execution). |
| `server/strategies/statistical_arbitrage.py` | `analyze_statistical_arbitrage` | Basket deviation threshold rules with exits. |
| `server/strategies/vix_term_structure.py` | `analyze_vix_term_structure` | Contango/backwardation threshold regimes. |
| `server/strategies/volatility_regime.py` | `analyze_volatility_regime` | Volatility regime switching by high/low threshold bands. |

## 3) Hybrid / orchestration tools

| Module | Primary MCP tools | Classification note |
|---|---|---|
| `server/strategies/comprehensive_analysis.py` | `generate_comprehensive_analysis_report` | Hybrid: orchestrates multiple strategy outputs (includes score-based and rule-based interpretations). |
| `server/strategies/unified_market_scanner.py` | `market_scanner` | Hybrid: combines strategy performance with current signals and aggregates across methods. |
| `server/strategies/comprehensive_market_scanner.py` | scanner helper logic | Hybrid legacy helper/orchestrator around several strategy implementations. |
| `server/strategies/fundamental_analysis.py` | `generate_fundamental_analysis_report`, `index_financial_statement_rows` | Analysis-focused (fundamental metrics/insights), not a trading-score strategy model. |

## 4) Practical implication for ADK reporting

- **Score-driven routes** are best for statements like: score trend, component attribution, and score-threshold recommendation.
- **Rule-driven routes** are best for statements like: trigger conditions hit/missed, event frequencies, regime transitions, and realized trade metrics.
- **Hybrid routes** should be described as synthesized outputs that depend on both score-based and rule-based building blocks.

## 5) Source of truth

- Tool registration: `server/tool_registry.py`
- Taxonomy contract: `docs/analysis_strategy_catalog.json`
- ADK wrappers: `stock_analyzer_bot/mcp_tools.py`
