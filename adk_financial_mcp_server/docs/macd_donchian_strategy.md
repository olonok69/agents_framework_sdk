# MACD + Donchian Strategy

## What the Strategy Does
- Evaluates a MACD + Donchian strategy and compares performance against buy-and-hold.
- Produces strategy-level performance metrics and current recommendation output.

## Trading Logic (Current MCP Strategy)
- Computes MACD line, signal line, and histogram from close prices.
- Computes Donchian channel position using rolling `window` highs/lows.
- Builds component scores:
	- MACD score from line-vs-signal relative position.
	- Donchian score from channel position.
- Combines into a weighted score and maps to signal:
	- BUY when combined score > 25
	- SELL when combined score < -25
	- otherwise HOLD
- Backtests signal-following returns versus buy-and-hold.

## Data & Indicators
- Source: Yahoo Finance OHLCV via `yfinance`.
- Inputs:
	- `symbol`
	- `period`
	- `fast_period`, `slow_period`, `signal_period`
	- `window` (Donchian)

## Outputs (MCP Tool)
- Performance comparison report with:
	- strategy return, buy-and-hold return, excess return
	- volatility, Sharpe, max drawdown
	- win rate, trade count, average trade return
- Current status block with MACD score, Donchian score, combined score, and signal.

## Implementation in This Repo
- MCP strategy tool:
	- `analyze_macd_donchian_performance` in `server/strategies/performance_tools.py`
- ADK wrapper:
	- `macd_donchian_analysis` in `stock_analyzer_bot/mcp_tools.py`
- ADK runner:
	- `run_macd_donchian_analysis` in `stock_analyzer_bot/adk_bot.py`
- API endpoint:
	- `POST /macd_donchian` in `stock_analyzer_bot/api.py`
- Django action:
	- `macd_donchian` in `django_ui/analyzer/views.py`

## Key Parameters
- `symbol`
- `period`
- `fast_period`, `slow_period`, `signal_period`
- `window` (Donchian channel window)

## API Example
```json
{
	"symbol": "AAPL",
	"period": "1y",
	"fast_period": 12,
	"slow_period": 26,
	"signal_period": 9,
	"window": 20
}
```

## Notes
- App integration now uses the strategy/performance MCP tool for MACD Donchian.
- Legacy scoring-oriented tooling may still exist for other internal flows, but this API/UI entry is strategy-oriented.
