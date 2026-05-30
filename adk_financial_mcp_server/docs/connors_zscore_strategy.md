# Connors RSI + Z-Score Strategy

## What the Strategy Measures
- Short-term mean reversion combining Connors RSI components with a statistical Z-Score overlay.
- Targets stretched moves that may revert over a few sessions.

## Data & Prep
- Source: Yahoo Finance OHLCV via `yfinance` (daily candles, configurable period).
- Typical defaults: `period=1y`, `rsi_period=3`, `streak_period=2`, `rank_period=100`, `zscore_window=20`, weights (connors_weight=0.7, zscore_weight=0.3).

## Computation
- Connors RSI components:
  - Price RSI over `rsi_period`.
  - Streak RSI over `streak_period` (up/down run length).
  - Percent rank of daily returns over `rank_period`.
- Combine the three into a Connors RSI score.
- Compute Z-Score of returns/prices over `zscore_window`.
- Blend Connors RSI and Z-Score using provided weights; derive signal bands (overbought/oversold) and a composite score.

## Outputs (MCP Tool)
- Metrics: composite score, signal (BUY/SELL/HOLD), returns vs. buy-and-hold, Sharpe, max drawdown.
- Interpretation on overbought/oversold state, risk note, and expected mean-reversion behavior.

## Implementation in This Repo
- MCP tool: `analyze_connors_zscore_performance` in `server/strategies/connors_zscore.py`.
- Smolagents wrapper: `connors_zscore_analysis` in `stock_analyzer_bot/tools.py`.
- Used in ToolCallingAgent and CodeAgent flows; reachable via `/technical`, `/scanner`, `/multisector`, `/combined`.

## Key Parameters
- `period`: data lookback (e.g., 6mo, 1y).
- `rsi_period`, `streak_period`, `rank_period`: Connors RSI components.
- `zscore_window`: lookback for Z-Score.
- `connors_weight`, `zscore_weight`: blending weights.

## Quick Usage
- Wrapper call: `connors_zscore_analysis(symbol="AAPL", period="1y")`.
- Available in the Technical tab and Market Scanner.
