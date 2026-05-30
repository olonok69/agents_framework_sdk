# Unified Market Scanner (High-Level Tool)

## Purpose
- Single-call multi-stock scanner that runs the four technical strategies on every symbol, ranks opportunities, and returns a structured markdown report.

## Data & Sources
- Yahoo Finance OHLCV via `yfinance` (daily candles) for each symbol provided.
- User-configurable `period` (e.g., 6mo, 1y) and `output_format` (detailed/summary/executive).

## What It Produces
- Executive summary with market context.
- Ranked table of symbols with signals/ratings.
- Per-stock mini-sections with strategy highlights (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual MA).
- Portfolio-style recommendations and risk notes.

## Implementation in This Repo
- MCP tool: `market_scanner` in `server/strategies/unified_market_scanner.py` (registered in `server/main.py`).
- Smolagents wrapper: `unified_market_scanner` in `stock_analyzer_bot/tools.py` (HIGH_LEVEL_TOOLS).
- FastAPI: used by `/scanner` when `agent_type = "tool_calling"`; also invoked per sector in `/multisector` (tool-calling path).
- Streamlit: Market Scanner tab (ToolCallingAgent mode) calls this tool for multi-stock scans.

## Key Parameters
- `symbols`: comma-separated tickers (required).
- `period`: data lookback (default 1y).
- `output_format`: one of `detailed`, `summary`, `executive` (default detailed).

## Quick Usage
- Python wrapper: `unified_market_scanner(symbols="AAPL,MSFT,GOOGL", period="1y")`.
- FastAPI: `POST /scanner` with `agent_type="tool_calling"`.

## When to Use
- Fast, single-call ranking of many symbols with consistent formatting.
- Best for production scenarios where latency and cost matter more than granular control.
