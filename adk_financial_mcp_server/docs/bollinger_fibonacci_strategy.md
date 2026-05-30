# Bollinger Fibonacci Strategy

## What the Strategy Does
- Evaluates Bollinger-band mean-reversion behavior and compares performance versus buy-and-hold.
- Produces strategy-level metrics and recommendation output (not a pure scoring-only endpoint).

## Trading Logic (Current MCP Strategy)
- Computes Bollinger Bands from daily closes using:
	- `window` (default `20`)
	- `num_std` (default `2`)
- Derives `%B` position inside bands.
- Converts `%B` to a directional strategy score and maps to signals:
	- BUY when score > 25 (oversold bias)
	- SELL when score < -25 (overbought bias)
	- otherwise HOLD
- Backtests signal-following returns and compares to buy-and-hold.

## Data & Indicators
- Data source: Yahoo Finance daily OHLCV (`yfinance`).
- Inputs:
	- `symbol`
	- `period` (e.g., `6mo`, `1y`, `2y`, `5y`)
	- `window`
	- `num_std`
	- `window_swing_points` (accepted by app input for strategy consistency)

## Outputs
- Strategy performance report including:
	- strategy return, buy-and-hold return, excess return
	- volatility, Sharpe, max drawdown
	- win rate, total trades, avg trade return
- Current status block with `%B`, score, and signal recommendation.

## Implementation in This Repo
- MCP strategy tool:
	- `analyze_bollinger_fibonacci_performance` in `server/strategies/performance_tools.py`
- ADK wrapper:
	- `bollinger_fibonacci_analysis` in `stock_analyzer_bot/mcp_tools.py`
- ADK runner:
	- `run_bollinger_fibonacci_analysis` in `stock_analyzer_bot/adk_bot.py`
- API endpoint:
	- `POST /bollinger_fibonacci` in `stock_analyzer_bot/api.py`
- Django action:
	- `bollinger_fibonacci` in `django_ui/analyzer/views.py`

## API Example
```json
{
	"symbol": "AAPL",
	"period": "1y",
	"window": 20,
	"num_std": 2,
	"window_swing_points": 10
}
```

## Notes
- The app now uses the strategy/performance MCP tool for Bollinger Fibonacci analysis.
- Legacy scoring-style tooling can still exist internally for other flows, but this API/UI entry is strategy-oriented.
