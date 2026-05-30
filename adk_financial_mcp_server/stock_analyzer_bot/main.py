"""Stock Analyzer Bot - Google ADK multi-agent implementation."""
from __future__ import annotations

from .adk_bot import (
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_PROVIDER,
    run_bollinger_breakout_analysis,
    run_bollinger_fibonacci_analysis,
    run_bollinger_zscore_rsi_strategy_analysis,
    run_bollinger_zscore_analysis,
    run_combined_analysis,
    run_dual_moving_average_analysis,
    run_earnings_momentum_analysis,
    run_fundamental_analysis,
    run_gap_fade_analysis,
    run_macd_donchian_analysis,
    run_market_scanner,
    run_multi_timeframe_analysis,
    run_multi_sector_analysis,
    run_overnight_gap_analysis,
    run_pairs_trading_analysis,
    run_statistical_arbitrage_analysis,
    run_technical_analysis,
    run_trin_breadth_analysis,
    run_vix_term_structure_analysis,
    run_volatility_regime_analysis,
)

DEFAULT_MAX_STEPS = 25
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 8192

__all__ = [
    "run_technical_analysis",
    "run_market_scanner",
    "run_fundamental_analysis",
    "run_multi_sector_analysis",
    "run_combined_analysis",
    "run_earnings_momentum_analysis",
    "run_trin_breadth_analysis",
    "run_overnight_gap_analysis",
    "run_bollinger_breakout_analysis",
    "run_bollinger_fibonacci_analysis",
    "run_bollinger_zscore_rsi_strategy_analysis",
    "run_bollinger_zscore_analysis",
    "run_dual_moving_average_analysis",
    "run_gap_fade_analysis",
    "run_macd_donchian_analysis",
    "run_multi_timeframe_analysis",
    "run_pairs_trading_analysis",
    "run_statistical_arbitrage_analysis",
    "run_vix_term_structure_analysis",
    "run_volatility_regime_analysis",
    "DEFAULT_MODEL_ID",
    "DEFAULT_MODEL_PROVIDER",
    "DEFAULT_MAX_STEPS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
]
