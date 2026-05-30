"""Pairs trading strategy analysis tool for MCP server.

Approximation of qc_projects/main_pairs_trading.py using SPY/QQQ daily bars.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL_A = "SPY"
DEFAULT_SYMBOL_B = "QQQ"
DEFAULT_PERIOD = "2y"
DEFAULT_WINDOW = 20
DEFAULT_ENTRY_THRESHOLD = 2.0
DEFAULT_EXIT_THRESHOLD = 0.5
DEFAULT_POSITION_SIZE = 0.5
DEFAULT_WARMUP_PERIOD = 25
MAX_TRADES = 300


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


def _build_features(symbol_a: str, symbol_b: str, period: str, window: int, warmup_period: int) -> pd.DataFrame:
    a_df = _download_daily(symbol_a, period)
    b_df = _download_daily(symbol_b, period)

    out = pd.DataFrame(index=a_df.index.union(b_df.index).sort_values())
    out["a_close"] = a_df["Close"]
    out["b_close"] = b_df["Close"]
    out = out.dropna().copy()
    out["spread"] = out["a_close"] / out["b_close"]
    out["spread_mean"] = out["spread"].rolling(window).mean()
    out["spread_std"] = out["spread"].rolling(window).std(ddof=0)
    out["z_score"] = (out["spread"] - out["spread_mean"]) / out["spread_std"]
    out["z_score"] = out["z_score"].replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["z_score"]).copy()

    if warmup_period > 0 and len(out) > warmup_period:
        out = out.iloc[warmup_period:].copy()

    return out


def _simulate(
    features: pd.DataFrame,
    symbol_a: str,
    symbol_b: str,
    entry_threshold: float,
    exit_threshold: float,
    position_size: float,
) -> tuple[List[Dict], List[Dict]]:
    trades: List[Dict] = []
    signals: List[Dict] = []
    position = None

    for ts, row in features.iterrows():
        z = float(row["z_score"])
        a_px = float(row["a_close"])
        b_px = float(row["b_close"])

        if position is None:
            if z > entry_threshold:
                position = {
                    "side": f"short_{symbol_a.lower()}_long_{symbol_b.lower()}",
                    "entry_time": ts,
                    "entry_z": z,
                    "a_entry": a_px,
                    "b_entry": b_px,
                }
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "side": position["side"],
                        "z_score": round(z, 3),
                        "spread": round(float(row["spread"]), 6),
                    }
                )
            elif z < -entry_threshold:
                position = {
                    "side": f"long_{symbol_a.lower()}_short_{symbol_b.lower()}",
                    "entry_time": ts,
                    "entry_z": z,
                    "a_entry": a_px,
                    "b_entry": b_px,
                }
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "side": position["side"],
                        "z_score": round(z, 3),
                        "spread": round(float(row["spread"]), 6),
                    }
                )
        else:
            if abs(z) < exit_threshold:
                a_ret = a_px / float(position["a_entry"]) - 1.0
                b_ret = b_px / float(position["b_entry"]) - 1.0

                if str(position["side"]).startswith("short_"):
                    pnl = (-position_size * a_ret) + (position_size * b_ret)
                else:
                    pnl = (position_size * a_ret) + (-position_size * b_ret)

                trades.append(
                    {
                        "side": position["side"],
                        "entry_time": pd.Timestamp(position["entry_time"]).strftime("%Y-%m-%d"),
                        "exit_time": ts.strftime("%Y-%m-%d"),
                        "entry_z": round(float(position["entry_z"]), 3),
                        "exit_z": round(z, 3),
                        "entry_spread": round(float(position["a_entry"]) / float(position["b_entry"]), 6),
                        "exit_spread": round(float(row["spread"]), 6),
                        "return_pct": round(float(pnl) * 100, 3),
                    }
                )
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "exit",
                        "z_score": round(z, 3),
                        "spread": round(float(row["spread"]), 6),
                    }
                )
                position = None

    return trades, signals


def _metrics(features: pd.DataFrame, trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "spread_correlation": round(float(features["a_close"].corr(features["b_close"])), 4),
        }

    returns = [float(t["return_pct"]) for t in trades]
    return {
        "total_trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 3),
        "median_return_pct": round(float(np.median(returns)), 3),
        "best_trade_pct": round(float(max(returns)), 3),
        "worst_trade_pct": round(float(min(returns)), 3),
        "spread_correlation": round(float(features["a_close"].corr(features["b_close"])), 4),
    }


def register_pairs_trading_tools(mcp):
    @mcp.tool()
    def analyze_pairs_trading(
        symbol_a: str = DEFAULT_SYMBOL_A,
        symbol_b: str = DEFAULT_SYMBOL_B,
        period: str = DEFAULT_PERIOD,
        window: int = DEFAULT_WINDOW,
        entry_threshold: float = DEFAULT_ENTRY_THRESHOLD,
        exit_threshold: float = DEFAULT_EXIT_THRESHOLD,
        position_size: float = DEFAULT_POSITION_SIZE,
        warmup_period: int = DEFAULT_WARMUP_PERIOD,
    ) -> str:
        """Analyze pairs trading mean-reversion strategy.

        Uses spread ratio symbol_a/symbol_b and z-score thresholds for entries/exits.
        """
        try:
            sym_a = symbol_a.upper().strip()
            sym_b = symbol_b.upper().strip()
            features = _build_features(sym_a, sym_b, period, window, warmup_period)
            trades, signals = _simulate(features, sym_a, sym_b, entry_threshold, exit_threshold, position_size)
            stats = _metrics(features, trades)

            summary = (
                f"### Pairs Trading Overview ({sym_a}/{sym_b})\n"
                f"- Period: {period} | Window: {window} | Position size: {position_size:.2f}\n"
                f"- Entry: z > +{entry_threshold} (short {sym_a}/long {sym_b}) or z < -{entry_threshold} (long {sym_a}/short {sym_b})\n"
                f"- Exit: |z| < {exit_threshold}\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}%\n"
                f"- Avg return: {stats['avg_return_pct']:+.3f}% | Median return: {stats['median_return_pct']:+.3f}%\n"
                f"- Best/Worst: {stats['best_trade_pct']:+.3f}% / {stats['worst_trade_pct']:+.3f}% | Corr: {stats['spread_correlation']:.4f}"
            )

            payload = {
                "pair": f"{sym_a}/{sym_b}",
                "period": period,
                "parameters": {
                    "window": window,
                    "entry_threshold": entry_threshold,
                    "exit_threshold": exit_threshold,
                    "position_size": position_size,
                    "warmup_period": warmup_period,
                },
                "metrics": stats,
                "trades": trades[-MAX_TRADES:],
                "signals": signals[-MAX_TRADES:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Pairs trading analysis failed: {exc}"})

    return mcp
