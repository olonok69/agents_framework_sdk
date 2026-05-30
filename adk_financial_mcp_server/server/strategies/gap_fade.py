"""Gap Fade strategy analysis tool for MCP server.

Approximation of qc_projects/main_gap_fade.py using daily OHLCV data.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL = "SPY"
DEFAULT_PERIOD = "2y"
DEFAULT_GAP_THRESHOLD = 0.02
DEFAULT_HOLD_MINUTES = 120
DEFAULT_POSITION_SIZE = 0.8
TRADING_MINUTES = 390
MAX_TRADES = 300


def _download_daily(symbol: str, period: str) -> pd.DataFrame:
    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        progress=False,
        multi_level_index=False,
    )
    if data is None or data.empty:
        raise ValueError(f"No OHLCV data for {symbol}")
    return data[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()


def _compute_gap_frame(df: pd.DataFrame, gap_threshold: float) -> pd.DataFrame:
    out = df.copy()
    out["prev_close"] = out["Close"].shift(1)
    out = out.dropna(subset=["prev_close"]).copy()
    out["gap_pct"] = (out["Open"] - out["prev_close"]) / out["prev_close"]
    out["gap_direction"] = np.where(out["gap_pct"] > 0, "up", "down")
    out.loc[out["gap_pct"].abs() < gap_threshold, "gap_direction"] = "none"
    out["entry_side"] = np.where(
        out["gap_direction"] == "up",
        "short",
        np.where(out["gap_direction"] == "down", "long", "flat"),
    )
    return out


def _simulate_gap_fade(
    gap_df: pd.DataFrame,
    hold_minutes: int,
    position_size: float,
) -> tuple[List[Dict], List[Dict]]:
    time_fraction = min(hold_minutes / TRADING_MINUTES, 1.0)
    trades: List[Dict] = []
    signals: List[Dict] = []

    for as_of, row in gap_df.iterrows():
        if row["entry_side"] == "flat":
            continue

        entry_price = float(row["Open"])
        direction = str(row["entry_side"])

        stop_hit = False
        exit_reason = "time"

        if direction == "short":
            stop_hit = float(row["High"]) > entry_price
            if stop_hit:
                exit_price = float(row["High"])
                minutes_held = 0
                exit_reason = "stop"
            else:
                exit_price = entry_price + (float(row["Close"]) - float(row["Open"])) * time_fraction
                minutes_held = hold_minutes
            ret_pct = (entry_price - exit_price) / entry_price * 100
        else:
            stop_hit = float(row["Low"]) < entry_price
            if stop_hit:
                exit_price = float(row["Low"])
                minutes_held = 0
                exit_reason = "stop"
            else:
                exit_price = entry_price + (float(row["Close"]) - float(row["Open"])) * time_fraction
                minutes_held = hold_minutes
            ret_pct = (exit_price - entry_price) / entry_price * 100

        trades.append(
            {
                "date": as_of.strftime("%Y-%m-%d"),
                "direction": direction,
                "gap_pct": round(float(row["gap_pct"]) * 100, 3),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "return_pct": round(ret_pct, 2),
                "stop_hit": bool(stop_hit),
                "exit_reason": exit_reason,
                "minutes_held": int(minutes_held),
                "position_size": round(position_size, 2),
            }
        )

        signals.append(
            {
                "date": as_of.strftime("%Y-%m-%d"),
                "direction": direction,
                "gap_pct": round(float(row["gap_pct"]) * 100, 3),
                "stop_hit": bool(stop_hit),
                "return_pct": round(ret_pct, 2),
            }
        )

    return trades, signals


def _metrics(trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "stop_rate_pct": 0.0,
        }

    returns = [float(t["return_pct"]) for t in trades]
    stop_hits = [bool(t["stop_hit"]) for t in trades]
    return {
        "total_trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 2),
        "median_return_pct": round(float(np.median(returns)), 2),
        "stop_rate_pct": round(sum(1 for s in stop_hits if s) / len(stop_hits) * 100, 1),
    }


def register_gap_fade_tools(mcp):
    @mcp.tool()
    def analyze_gap_fade(
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        gap_threshold: float = DEFAULT_GAP_THRESHOLD,
        hold_minutes: int = DEFAULT_HOLD_MINUTES,
        position_size: float = DEFAULT_POSITION_SIZE,
    ) -> str:
        """Analyze an intraday gap-fade strategy approximation.

        Entry at open for abs(gap) >= threshold:
        - gap up -> short
        - gap down -> long
        Exit on stop (gap extreme break) or time exit at hold_minutes approximation.
        """
        try:
            frame = _download_daily(symbol.upper(), period)
            gap_frame = _compute_gap_frame(frame, gap_threshold)
            trades, signals = _simulate_gap_fade(gap_frame, hold_minutes, position_size)
            stats = _metrics(trades)

            summary = (
                f"### Gap Fade Overview ({symbol.upper()})\n"
                f"- Period: {period} | Gap threshold: {gap_threshold:.2%} | Hold: {hold_minutes} minutes\n"
                f"- Position size: {position_size:.0%}\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}%\n"
                f"- Avg return: {stats['avg_return_pct']:+.2f}% | Median return: {stats['median_return_pct']:+.2f}%\n"
                f"- Stop rate: {stats['stop_rate_pct']:.1f}%"
            )

            payload = {
                "symbol": symbol.upper(),
                "period": period,
                "parameters": {
                    "gap_threshold": gap_threshold,
                    "hold_minutes": hold_minutes,
                    "position_size": position_size,
                },
                "metrics": stats,
                "trades": trades[-MAX_TRADES:],
                "signals": signals[-MAX_TRADES:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Gap fade analysis failed: {exc}"})

    return mcp
