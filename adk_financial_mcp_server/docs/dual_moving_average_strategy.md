# Dual Moving Average Strategy

## What the Strategy Does
- Evaluates trend-following behavior with short/long moving-average crossovers.
- Compares strategy performance against buy-and-hold and reports current regime signal.

## Trading Logic (Current MCP Strategy)
- Computes short and long moving averages using configured `ma_type` (`SMA` or `EMA`).
- Generates crossover signals:
	- Golden Cross: short MA crosses above long MA → BUY
	- Death Cross: short MA crosses below long MA → SELL
- Tracks position and backtests signal-following returns over the selected period.

## Data & Indicators
- Source: Yahoo Finance OHLCV (`yfinance`).
- Inputs:
	- `symbol`
	- `period`
	- `short_period`, `long_period`
	- `ma_type` (`SMA` or `EMA`)

## Outputs (MCP Tool)
- Performance report including:
	- strategy return, buy-and-hold return, excess return
	- Sharpe, max drawdown, volatility
	- trade count, win rate, recent crossover context
- Current state:
	- position, signal, trend direction, trend strength

## Implementation in This Repo
- MCP strategy tool:
	- `analyze_dual_ma_strategy` in `server/strategies/performance_tools.py`
- ADK wrapper:
	- `dual_moving_average_analysis` in `stock_analyzer_bot/mcp_tools.py`
- ADK runner:
	- `run_dual_moving_average_analysis` in `stock_analyzer_bot/adk_bot.py`
- API endpoint:
	- `POST /dual_moving_average` in `stock_analyzer_bot/api.py`
- Django action:
	- `dual_moving_average` in `django_ui/analyzer/views.py`

## Key Parameters
- `symbol`
- `period`
- `short_period`, `long_period`
- `ma_type`

## API Example
```json
{
	"symbol": "AAPL",
	"period": "5y",
	"short_period": 50,
	"long_period": 200,
	"ma_type": "SMA"
}
```

## Notes
- Endpoint uses ADK-first analysis with a safe fallback formatter if ADK returns an invalid “no data access” style response.
