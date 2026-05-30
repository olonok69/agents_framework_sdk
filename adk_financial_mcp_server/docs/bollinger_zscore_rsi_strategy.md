# Bollinger Z-Score + RSI Strategy

## What the Strategy Does
- Mean-reversion trading strategy that combines Bollinger Z-Score and RSI confirmation.
- Uses explicit entry/exit rules and produces trade-level backtest-style outputs.

## Trading Logic
- **Entry (Long):**
  - `zscore <= zscore_buy_threshold` (default `-2.0`)
  - `rsi <= rsi_oversold` (default `30`)
- **Exit (Close Long):**
  - `zscore >= zscore_sell_threshold` (default `2.0`)
  - `rsi >= rsi_overbought` (default `70`)

## Data & Indicators
- Data source: Yahoo Finance daily OHLCV (`yfinance`).
- Bollinger inputs:
  - `bb_window` (default `20`)
  - `bb_std` (default `2.0`)
- RSI input:
  - `rsi_period` (default `14`, Wilder smoothing)
- Derived fields:
  - Rolling mean and sigma
  - Bollinger upper/lower bands
  - Z-Score: `(Close - rolling_mean) / rolling_sigma`
  - RSI

## Outputs
- Summary text for quick interpretation.
- Structured metrics payload including:
  - `total_trades`, `win_rate_pct`, `avg_return_pct`, `median_return_pct`
  - `best_trade_pct`, `worst_trade_pct`, `avg_holding_days`
  - `strategy_return_pct`, `buy_hold_return_pct`, `excess_return_pct`
- Latest snapshot:
  - latest price, latest z-score, latest RSI, current signal (`BUY`/`SELL`/`HOLD`)
- Detailed `trades` and `signals` arrays.

## Implementation in This Repo
- MCP strategy tool:
  - `analyze_bollinger_zscore_rsi_strategy` in `server/strategies/bollinger_zscore_rsi.py`
- MCP registration:
  - `register_bollinger_zscore_rsi_tools` in `server/tool_registry.py`
- ADK wrapper:
  - `bollinger_zscore_rsi_strategy_analysis` in `stock_analyzer_bot/mcp_tools.py`
- ADK runner:
  - `run_bollinger_zscore_rsi_strategy_analysis` in `stock_analyzer_bot/adk_bot.py`
- API endpoint:
  - `POST /bollinger_zscore_rsi` in `stock_analyzer_bot/api.py`
- Django UI action:
  - `bollinger_zscore_rsi` in `django_ui/analyzer/views.py`

## Parameters
- `symbol` (default `AAPL`)
- `period` (default `2y`)
- `bb_window`, `bb_std`
- `rsi_period`, `rsi_oversold`, `rsi_overbought`
- `zscore_buy_threshold`, `zscore_sell_threshold`

## API Example
```json
{
  "symbol": "AAPL",
  "period": "2y",
  "bb_window": 20,
  "bb_std": 2.0,
  "rsi_period": 14,
  "rsi_oversold": 30.0,
  "rsi_overbought": 70.0,
  "zscore_buy_threshold": -2.0,
  "zscore_sell_threshold": 2.0
}
```

## Notes
- This strategy entry is separate from legacy scoring tools and does not replace them.
- The notebook under `notebooks/bollinger_zscore_rsi/` is useful for indicator exploration, but the production strategy path is the MCP tool above.
