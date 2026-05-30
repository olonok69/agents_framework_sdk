"""Statistical arbitrage strategy analysis tool for MCP server.

Approximation of qc_projects/main_statistical_arbitrage.py using daily OHLCV bars.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOLS = "AAPL,MSFT,GOOGL"
DEFAULT_PERIOD = "2y"
DEFAULT_WINDOW = 20
DEFAULT_ENTRY_THRESHOLD = 1.5
DEFAULT_EXIT_THRESHOLD = 0.3
DEFAULT_POSITION_SIZE = 0.3
DEFAULT_WARMUP_PERIOD = 25
MAX_EVENTS = 400


def _parse_symbols(symbols: str) -> List[str]:
    parsed = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(parsed) < 3:
        raise ValueError("At least 3 symbols are required for statistical arbitrage")
    return parsed


def _download_daily(symbol: str, period: str) -> pd.DataFrame:
    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        progress=False,
        multi_level_index=False,
        auto_adjust=False,
    )
    if data is None or data.empty:
        raise ValueError(f"No OHLCV data for {symbol}")
    frame = data[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame


def _build_close_frame(symbols: List[str], period: str, window: int, warmup_period: int) -> pd.DataFrame:
    closes = {}
    for sym in symbols:
        closes[sym] = _download_daily(sym, period)["Close"]

    frame = pd.DataFrame(closes).dropna().copy()

    for sym in symbols:
        roll_mean = frame[sym].rolling(window).mean()
        roll_std = frame[sym].rolling(window).std(ddof=0)
        z = (frame[sym] - roll_mean) / roll_std
        frame[f"z_{sym}"] = z.replace([np.inf, -np.inf], np.nan)

    z_cols = [f"z_{s}" for s in symbols]
    frame = frame.dropna(subset=z_cols).copy()
    frame["basket_mean"] = frame[z_cols].mean(axis=1)

    for sym in symbols:
        frame[f"dev_{sym}"] = frame[f"z_{sym}"] - frame["basket_mean"]

    if warmup_period > 0 and len(frame) > warmup_period:
        frame = frame.iloc[warmup_period:].copy()

    return frame


def _simulate(
    frame: pd.DataFrame,
    symbols: List[str],
    entry_threshold: float,
    exit_threshold: float,
    position_size: float,
) -> tuple[List[Dict], List[Dict]]:
    positions: Dict[str, Dict] = {}
    trades: List[Dict] = []
    signals: List[Dict] = []

    for ts, row in frame.iterrows():
        for sym in symbols:
            dev = float(row[f"dev_{sym}"])
            px = float(row[sym])
            open_pos = positions.get(sym)

            if open_pos is None:
                if dev < -entry_threshold:
                    positions[sym] = {
                        "side": "long",
                        "entry_time": ts,
                        "entry_price": px,
                        "entry_dev": dev,
                    }
                    signals.append(
                        {
                            "timestamp": ts.strftime("%Y-%m-%d"),
                            "symbol": sym,
                            "type": "entry",
                            "side": "long",
                            "deviation": round(dev, 4),
                        }
                    )
                elif dev > entry_threshold:
                    positions[sym] = {
                        "side": "short",
                        "entry_time": ts,
                        "entry_price": px,
                        "entry_dev": dev,
                    }
                    signals.append(
                        {
                            "timestamp": ts.strftime("%Y-%m-%d"),
                            "symbol": sym,
                            "type": "entry",
                            "side": "short",
                            "deviation": round(dev, 4),
                        }
                    )
            else:
                if abs(dev) < exit_threshold:
                    raw_ret = px / float(open_pos["entry_price"]) - 1.0
                    signed_ret = raw_ret if open_pos["side"] == "long" else -raw_ret
                    weighted_ret_pct = signed_ret * float(position_size) * 100
                    trades.append(
                        {
                            "symbol": sym,
                            "side": open_pos["side"],
                            "entry_time": pd.Timestamp(open_pos["entry_time"]).strftime("%Y-%m-%d"),
                            "exit_time": ts.strftime("%Y-%m-%d"),
                            "entry_price": round(float(open_pos["entry_price"]), 2),
                            "exit_price": round(px, 2),
                            "entry_deviation": round(float(open_pos["entry_dev"]), 4),
                            "exit_deviation": round(dev, 4),
                            "return_pct": round(float(weighted_ret_pct), 3),
                        }
                    )
                    signals.append(
                        {
                            "timestamp": ts.strftime("%Y-%m-%d"),
                            "symbol": sym,
                            "type": "exit",
                            "deviation": round(dev, 4),
                        }
                    )
                    positions.pop(sym, None)

    return trades, signals


def _metrics(frame: pd.DataFrame, symbols: List[str], trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "avg_abs_deviation": round(float(np.mean([frame[f"dev_{s}"].abs().mean() for s in symbols])), 4),
        }

    returns = [float(t["return_pct"]) for t in trades]
    return {
        "total_trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 3),
        "median_return_pct": round(float(np.median(returns)), 3),
        "best_trade_pct": round(float(max(returns)), 3),
        "worst_trade_pct": round(float(min(returns)), 3),
        "avg_abs_deviation": round(float(np.mean([frame[f"dev_{s}"].abs().mean() for s in symbols])), 4),
    }


def register_statistical_arbitrage_tools(mcp):
    @mcp.tool()
    def analyze_statistical_arbitrage(
        symbols: str = DEFAULT_SYMBOLS,
        period: str = DEFAULT_PERIOD,
        window: int = DEFAULT_WINDOW,
        entry_threshold: float = DEFAULT_ENTRY_THRESHOLD,
        exit_threshold: float = DEFAULT_EXIT_THRESHOLD,
        position_size: float = DEFAULT_POSITION_SIZE,
        warmup_period: int = DEFAULT_WARMUP_PERIOD,
    ) -> str:
        """Analyze basket statistical arbitrage strategy.

        Computes per-symbol rolling z-scores, basket mean z-score, and trades deviations
        from basket mean using entry/exit thresholds.
        """
        try:
            parsed_symbols = _parse_symbols(symbols)
            frame = _build_close_frame(parsed_symbols, period, window, warmup_period)
            trades, signals = _simulate(frame, parsed_symbols, entry_threshold, exit_threshold, position_size)
            stats = _metrics(frame, parsed_symbols, trades)

            summary = (
                f"### Statistical Arbitrage Overview ({', '.join(parsed_symbols)})\n"
                f"- Period: {period} | Window: {window} | Position size: {position_size:.2f}\n"
                f"- Entry: deviation < -{entry_threshold} (long) or > +{entry_threshold} (short)\n"
                f"- Exit: |deviation| < {exit_threshold}\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}%\n"
                f"- Avg return: {stats['avg_return_pct']:+.3f}% | Median: {stats['median_return_pct']:+.3f}%\n"
                f"- Best/Worst: {stats['best_trade_pct']:+.3f}% / {stats['worst_trade_pct']:+.3f}% | Avg |dev|: {stats['avg_abs_deviation']:.4f}"
            )

            payload = {
                "symbols": parsed_symbols,
                "period": period,
                "parameters": {
                    "window": window,
                    "entry_threshold": entry_threshold,
                    "exit_threshold": exit_threshold,
                    "position_size": position_size,
                    "warmup_period": warmup_period,
                },
                "metrics": stats,
                "trades": trades[-MAX_EVENTS:],
                "signals": signals[-MAX_EVENTS:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Statistical arbitrage analysis failed: {exc}"})

    return mcp
