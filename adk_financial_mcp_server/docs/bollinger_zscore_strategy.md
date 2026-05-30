# Bollinger Z-Score (Mean Reversion) Strategy

## What the Strategy Measures
- Pure statistical mean reversion using Z-Score of price relative to a moving average.
- Flags overbought/oversold states based on standard deviation moves.

## Data & Prep
- Source: Yahoo Finance OHLCV via `yfinance` (daily candles, configurable period).
- Defaults: `period=1y`, `window=20`.

## Computation
- Compute rolling mean and standard deviation over `window`.
- Z-Score = (price − mean) / std.
- Classify zones: extreme oversold (Z < -2), oversold (Z < -1), neutral (|Z| < 1), overbought (Z > 1), extreme overbought (Z > 2).
- Optionally combine with basic trend/risk guards; derive signal and score.

## Outputs (MCP Tool)
- Metrics: score, BUY/SELL/HOLD signal, returns vs. buy-and-hold, Sharpe, max drawdown.
- Interpretation text on current Z-Score, distance from mean, and caution flags.

## Implementation in This Repo
- MCP tool: `analyze_bollinger_zscore_performance` in `server/strategies/bollinger_zscore.py`.
- Smolagents wrapper: `bollinger_zscore_analysis` (indirectly via strategy sets) and part of high-level reports.
- Used inside the comprehensive single-stock report and multi-stock scanner; accessible through ToolCallingAgent and CodeAgent flows.

## Key Parameters
- `period`: data lookback (e.g., 6mo, 1y, 2y).
- `window`: rolling window for mean/std (default 20).

## Quick Usage
- High-level call (included in comprehensive report): `comprehensive_performance_report(symbol="AAPL", period="1y")`.
- As part of multi-stock scanning: `unified_market_scanner(symbols="AAPL,MSFT,GOOGL", period="1y")`.
