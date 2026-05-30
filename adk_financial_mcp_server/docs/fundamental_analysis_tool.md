# Fundamental Analysis Tool (Low-Level)

## Purpose
- Generate a fundamentals-focused report from financial statements (income, balance sheet, cash flow) with ratios and narrative insights.
- Used both as a standalone analysis and inside combined (tech + fundamental) flows.

## Data & Sources
- Yahoo Finance fundamentals via `yfinance` (financials, balance sheet, cash flow).
- Period setting controls years of history (e.g., 3y, 5y, 1y).

## What It Produces
- Markdown report summarizing revenue, margins, profitability, leverage, liquidity, and cash flows.
- Key ratios (P/E, P/B, ROE, ROA, Current Ratio, Debt/Equity, etc.).
- Strengths, risks, and an overall recommendation.

## Implementation in This Repo
- MCP tool: `generate_fundamental_analysis_report` (alias `fundamental_analysis`) in `server/strategies/fundamental_analysis.py` (registered in `server/main.py`).
- Smolagents wrapper: `fundamental_analysis_report` in `stock_analyzer_bot/tools.py` (available to both agents).
- FastAPI: `/fundamental` (both agent types), and `/combined` (paired with technical) use this tool.
- Streamlit: Fundamental tab uses `/fundamental`; Combined tab uses `/combined` to merge technical + fundamental.

## Key Parameters
- `symbol`: ticker (required).
- `period`: years of data to pull (default 3y).

## Quick Usage
- Wrapper call: `fundamental_analysis_report(symbol="MSFT", period="3y")`.
- FastAPI: `POST /fundamental` or `POST /combined` (with `technical_period` and `fundamental_period`).

## When to Use
- Need a fundamentals-only view with ratios and narrative in one call.
- As the fundamental leg of the combined (tech + fundamental) workflow.
