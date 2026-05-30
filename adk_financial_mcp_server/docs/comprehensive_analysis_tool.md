# Comprehensive Performance Report (High-Level Tool)

## Purpose
- Single-call, multi-strategy technical report for one symbol.
- Runs the four underlying low-level strategies (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual Moving Average) and compiles an executive markdown report with metrics, signals, and guidance.

## Data & Sources
- Yahoo Finance OHLCV via `yfinance` (daily candles), user-configurable `period` (e.g., 3mo, 6mo, 1y, 2y, 5y).

## What It Produces
- Executive summary with overall recommendation and confidence.
- Per-strategy breakdown: score, signal (BUY/SELL/HOLD), returns vs. buy-and-hold, Sharpe, max drawdown, rationale.
- Aggregated comparison table and risk/position sizing notes.

## Implementation in This Repo
- MCP tool: `generate_comprehensive_analysis_report` in `server/strategies/comprehensive_analysis.py` (registered in `server/main.py`).
- Smolagents wrapper: `comprehensive_performance_report` in `stock_analyzer_bot/tools.py` (HIGH_LEVEL_TOOLS).
- FastAPI: used by `/technical` when `agent_type = "tool_calling"`.
- Streamlit: Technical tab (ToolCallingAgent mode) calls this tool for a single-stock analysis.

## Key Parameters
- `symbol`: ticker (required).
- `period`: data lookback (default 1y).

## Quick Usage
- Python wrapper: `comprehensive_performance_report(symbol="AAPL", period="1y")`.
- FastAPI: `POST /technical` with `agent_type="tool_calling"`.

## When to Use
- Fast, deterministic single-stock technical overview with one MCP call.
- Best for production-safe, low-latency, and low token/cost runs.
