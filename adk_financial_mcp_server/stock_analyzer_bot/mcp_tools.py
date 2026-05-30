"""MCP tool wrappers for the ADK stock analyzer runtime."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from .mcp_client import configure_session, get_session, shutdown_session

logger = logging.getLogger(__name__)


def configure_finance_tools(server_path: str | Path | None = None) -> None:
    """Configure finance tools."""

    configure_session(server_path)


def shutdown_finance_tools() -> None:
    """Shutdown finance tools."""

    shutdown_session()


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol values."""

    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must be a non-empty string")
    return cleaned


def _call_finance_tool(tool_name: str, parameters: Dict[str, object]) -> str:
    """Implement call finance tool."""

    try:
        return get_session().call_tool(tool_name, parameters)
    except Exception as exc:
        logger.exception("Error while calling %s", tool_name)
        return f"Error calling {tool_name}: {exc}"


def comprehensive_performance_report(symbol: str, period: str = "1y") -> str:
    """Implement comprehensive performance report."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("generate_comprehensive_analysis_report", params)


def unified_market_scanner(symbols: str, period: str = "1y", output_format: str = "detailed") -> str:
    """Implement unified market scanner."""

    params: Dict[str, object] = {
        "symbols": symbols,
        "period": period,
        "output_format": output_format,
    }
    return _call_finance_tool("market_scanner", params)


def fundamental_analysis_report(symbol: str, period: str = "3y") -> str:
    """Implement fundamental analysis report."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("generate_fundamental_analysis_report", params)


def earnings_momentum_analysis(
    symbols: str,
    period: str = "6mo",
    volume_window: int = 20,
    volume_multiplier: float = 2.0,
    hold_days: int = 5,
    max_positions: int = 3,
) -> str:
    """Implement earnings momentum analysis."""

    params: Dict[str, object] = {
        "symbols": symbols,
        "period": period,
        "volume_window": volume_window,
        "volume_multiplier": volume_multiplier,
        "hold_days": hold_days,
        "max_positions": max_positions,
    }
    return _call_finance_tool("analyze_earnings_momentum", params)


def trin_market_breadth_analysis(
    period: str = "6mo",
    window: int = 20,
    band_k: float = 1.5,
    use_log: bool = True,
) -> str:
    """Implement trin market breadth analysis."""

    params: Dict[str, object] = {
        "period": period,
        "window": window,
        "band_k": band_k,
        "use_log": use_log,
    }
    return _call_finance_tool("analyze_trin_market_breadth", params)


def overnight_gap_analysis(symbol: str, lookback_days: int = 120, min_gap_pct: float = 1.0) -> str:
    """Implement overnight gap analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "lookback_days": lookback_days,
        "min_gap_pct": min_gap_pct,
    }
    return _call_finance_tool("analyze_overnight_gaps", params)


def bollinger_breakout_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_period: int = 14,
    volume_window: int = 20,
    volume_multiplier: float = 1.2,
    warmup_bars: int = 25,
) -> str:
    """Implement bollinger breakout analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "bb_period": bb_period,
        "bb_std": bb_std,
        "atr_period": atr_period,
        "volume_window": volume_window,
        "volume_multiplier": volume_multiplier,
        "warmup_bars": warmup_bars,
    }
    return _call_finance_tool("analyze_bollinger_breakout", params)


def gap_fade_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    gap_threshold: float = 0.02,
    hold_minutes: int = 120,
    position_size: float = 0.8,
) -> str:
    """Implement gap fade analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "gap_threshold": gap_threshold,
        "hold_minutes": hold_minutes,
        "position_size": position_size,
    }
    return _call_finance_tool("analyze_gap_fade", params)


def multi_timeframe_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    sma_fast: int = 50,
    sma_slow: int = 200,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_exit: float = 70.0,
    warmup_days: int = 210,
) -> str:
    """Implement multi timeframe analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "rsi_period": rsi_period,
        "rsi_oversold": rsi_oversold,
        "rsi_exit": rsi_exit,
        "warmup_days": warmup_days,
    }
    return _call_finance_tool("analyze_multi_timeframe", params)


def pairs_trading_analysis(
    symbol_a: str = "SPY",
    symbol_b: str = "QQQ",
    period: str = "2y",
    window: int = 20,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    position_size: float = 0.5,
    warmup_period: int = 25,
) -> str:
    """Implement pairs trading analysis."""

    params: Dict[str, object] = {
        "symbol_a": _normalize_symbol(symbol_a),
        "symbol_b": _normalize_symbol(symbol_b),
        "period": period,
        "window": window,
        "entry_threshold": entry_threshold,
        "exit_threshold": exit_threshold,
        "position_size": position_size,
        "warmup_period": warmup_period,
    }
    return _call_finance_tool("analyze_pairs_trading", params)


def statistical_arbitrage_analysis(
    symbols: str = "AAPL,MSFT,GOOGL",
    period: str = "2y",
    window: int = 20,
    entry_threshold: float = 1.5,
    exit_threshold: float = 0.3,
    position_size: float = 0.3,
    warmup_period: int = 25,
) -> str:
    """Implement statistical arbitrage analysis."""

    params: Dict[str, object] = {
        "symbols": symbols,
        "period": period,
        "window": window,
        "entry_threshold": entry_threshold,
        "exit_threshold": exit_threshold,
        "position_size": position_size,
        "warmup_period": warmup_period,
    }
    return _call_finance_tool("analyze_statistical_arbitrage", params)


def vix_term_structure_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    front_window: int = 10,
    back_window: int = 30,
    contango_threshold: float = 1.05,
    backwardation_threshold: float = 0.95,
    long_position_size: float = 0.8,
    short_position_size: float = -0.5,
    warmup_period: int = 35,
) -> str:
    """Implement vix term structure analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "front_window": front_window,
        "back_window": back_window,
        "contango_threshold": contango_threshold,
        "backwardation_threshold": backwardation_threshold,
        "long_position_size": long_position_size,
        "short_position_size": short_position_size,
        "warmup_period": warmup_period,
    }
    return _call_finance_tool("analyze_vix_term_structure", params)


def volatility_regime_analysis(
    period: str = "2y",
    spy_symbol: str = "SPY",
    qqq_symbol: str = "QQQ",
    arkk_symbol: str = "ARKK",
    tlt_symbol: str = "TLT",
    gld_symbol: str = "GLD",
    vol_window: int = 20,
    high_vol_threshold: float = 25.0,
    low_vol_threshold: float = 15.0,
    warmup_period: int = 25,
) -> str:
    """Implement volatility regime analysis."""

    params: Dict[str, object] = {
        "period": period,
        "spy_symbol": _normalize_symbol(spy_symbol),
        "qqq_symbol": _normalize_symbol(qqq_symbol),
        "arkk_symbol": _normalize_symbol(arkk_symbol),
        "tlt_symbol": _normalize_symbol(tlt_symbol),
        "gld_symbol": _normalize_symbol(gld_symbol),
        "vol_window": vol_window,
        "high_vol_threshold": high_vol_threshold,
        "low_vol_threshold": low_vol_threshold,
        "warmup_period": warmup_period,
    }
    return _call_finance_tool("analyze_volatility_regime", params)


def bollinger_zscore_analysis(symbol: str = "AAPL", period: int = 20) -> str:
    """Implement bollinger zscore analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("calculate_bollinger_z_score", params)


def bollinger_zscore_rsi_strategy_analysis(
    symbol: str = "AAPL",
    period: str = "2y",
    bb_window: int = 20,
    bb_std: float = 2.0,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    zscore_buy_threshold: float = -2.0,
    zscore_sell_threshold: float = 2.0,
) -> str:
    """Implement bollinger zscore rsi strategy analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "bb_window": bb_window,
        "bb_std": bb_std,
        "rsi_period": rsi_period,
        "rsi_oversold": rsi_oversold,
        "rsi_overbought": rsi_overbought,
        "zscore_buy_threshold": zscore_buy_threshold,
        "zscore_sell_threshold": zscore_sell_threshold,
    }
    return _call_finance_tool("analyze_bollinger_zscore_rsi_strategy", params)


def bollinger_fibonacci_analysis(
    symbol: str = "AAPL",
    period: str = "1y",
    window: int = 20,
    num_std: int = 2,
    window_swing_points: int = 10,
) -> str:
    """Implement bollinger fibonacci analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "window": window,
        "num_std": num_std,
        "window_swing_points": window_swing_points,
    }
    return _call_finance_tool("analyze_bollinger_fibonacci_performance", params)


def macd_donchian_analysis(
    symbol: str = "AAPL",
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    window: int = 20,
) -> str:
    """Implement macd donchian analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "window": window,
    }
    return _call_finance_tool("analyze_macd_donchian_performance", params)


def dual_moving_average_analysis(
    symbol: str = "AAPL",
    period: str = "2y",
    short_period: int = 50,
    long_period: int = 200,
    ma_type: str = "SMA",
) -> str:
    """Implement dual moving average analysis."""

    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "short_period": short_period,
        "long_period": long_period,
        "ma_type": ma_type,
    }
    return _call_finance_tool("analyze_dual_ma_strategy", params)
