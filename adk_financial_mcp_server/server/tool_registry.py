"""Centralized tool registration for the finance MCP server."""
from __future__ import annotations

from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from strategies.bollinger_fibonacci import register_bollinger_fibonacci_tools
from strategies.macd_donchian import register_macd_donchian_tools
from strategies.connors_zscore import register_connors_zscore_tools
from strategies.dual_moving_average import register_dual_ma_tools
from strategies.bollinger_zscore import register_bollinger_zscore_tools
from strategies.bollinger_zscore_rsi import register_bollinger_zscore_rsi_tools
from strategies.fundamental_analysis import add_fundamental_analysis_tool, add_financial_statement_index_tool
from strategies.trin_strategy import register_trin_strategy_tools
from strategies.gap_strategy import register_gap_strategy_tools
from strategies.earnings_momentum import register_earnings_momentum_tools
from strategies.bollinger_breakout import register_bollinger_breakout_tools
from strategies.gap_fade import register_gap_fade_tools
from strategies.multi_timeframe import register_multi_timeframe_tools
from strategies.pairs_trading import register_pairs_trading_tools
from strategies.statistical_arbitrage import register_statistical_arbitrage_tools
from strategies.vix_term_structure import register_vix_term_structure_tools
from strategies.volatility_regime import register_volatility_regime_tools
from strategies.performance_tools import add_all_performance_tools
from strategies.comprehensive_analysis import add_comprehensive_strategy_analysis_tool
from strategies.unified_market_scanner import add_unified_market_scanner_tool

ToolRegistrar = Callable[[FastMCP], None]


def get_default_registrars() -> list[ToolRegistrar]:
    return [
        register_bollinger_fibonacci_tools,
        register_macd_donchian_tools,
        register_connors_zscore_tools,
        register_dual_ma_tools,
        register_bollinger_zscore_tools,
        register_bollinger_zscore_rsi_tools,
        register_trin_strategy_tools,
        register_gap_strategy_tools,
        register_earnings_momentum_tools,
        register_bollinger_breakout_tools,
        register_gap_fade_tools,
        register_multi_timeframe_tools,
        register_pairs_trading_tools,
        register_statistical_arbitrage_tools,
        register_vix_term_structure_tools,
        register_volatility_regime_tools,
        add_all_performance_tools,
        add_comprehensive_strategy_analysis_tool,
        add_unified_market_scanner_tool,
        add_fundamental_analysis_tool,
        add_financial_statement_index_tool,
    ]


def register_all_tools(mcp: FastMCP, registrars: list[ToolRegistrar] | None = None) -> None:
    for register in registrars or get_default_registrars():
        register(mcp)
