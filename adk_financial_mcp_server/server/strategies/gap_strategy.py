"""
Overnight gap analysis (gap-up / gap-down) for MCP server.

Calculates daily gaps from prior close to next open, classifies up/down, and
reports intraday fill rates and summary metrics.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_LOOKBACK_DAYS = 120
DEFAULT_MIN_GAP_PCT = 1.0  # percent
MAX_SERIES = 200


def _fetch_daily(symbol: str, lookback_days: int) -> pd.DataFrame:
    period = f"{max(lookback_days + 5, 30)}d"
    data = yf.download(symbol, period=period, interval="1d", progress=False, multi_level_index=False)
    if data is None or data.empty:
        raise ValueError(f"No daily data for {symbol}")
    return data.tail(lookback_days + 1)  # need previous close


def _compute_gaps(df: pd.DataFrame, min_gap_pct: float) -> List[Dict]:
    rows = []
    closes = df["Close"].values
    opens = df["Open"].values
    highs = df["High"].values
    lows = df["Low"].values
    dates = df.index

    for i in range(1, len(df)):
        prev_close = closes[i - 1]
        today_open = opens[i]
        gap_pct = (today_open - prev_close) / prev_close * 100
        if abs(gap_pct) < min_gap_pct:
            continue
        direction = "up" if gap_pct > 0 else "down"

        # intraday fill relative to prior close
        filled = False
        if direction == "up" and lows[i] <= prev_close:
            filled = True
        if direction == "down" and highs[i] >= prev_close:
            filled = True

        same_day_close_ret = (closes[i] - today_open) / today_open * 100
        rows.append({
            "date": dates[i].strftime("%Y-%m-%d"),
            "gap_pct": float(round(gap_pct, 3)),
            "direction": direction,
            "filled": filled,
            "prev_close": float(round(prev_close, 4)),
            "open": float(round(today_open, 4)),
            "high": float(round(highs[i], 4)),
            "low": float(round(lows[i], 4)),
            "close": float(round(closes[i], 4)),
            "same_day_close_ret": float(round(same_day_close_ret, 3)),
        })
    return rows


def _aggregate(rows: List[Dict]) -> Dict:
    if not rows:
        return {}
    total = len(rows)
    up = [r for r in rows if r["direction"] == "up"]
    down = [r for r in rows if r["direction"] == "down"]
    filled = [r for r in rows if r["filled"]]

    def avg(key, subset=None):
        subset = subset if subset is not None else rows
        vals = [r[key] for r in subset]
        return float(round(np.mean(vals), 3)) if vals else 0.0

    metrics = {
        "total_gaps": total,
        "up_gaps": len(up),
        "down_gaps": len(down),
        "fill_rate_all": float(round(len(filled) / total * 100, 1)),
        "fill_rate_up": float(round(len([r for r in up if r["filled"]]) / len(up) * 100, 1)) if up else 0.0,
        "fill_rate_down": float(round(len([r for r in down if r["filled"]]) / len(down) * 100, 1)) if down else 0.0,
        "avg_gap_pct": avg("gap_pct"),
        "avg_gap_up_pct": avg("gap_pct", up) if up else 0.0,
        "avg_gap_down_pct": avg("gap_pct", down) if down else 0.0,
        "avg_same_day_close_ret": avg("same_day_close_ret"),
    }

    # Recent notable gaps (last 5)
    metrics["recent"] = rows[-5:][::-1]
    return metrics


def register_gap_strategy_tools(mcp):
    """Register overnight gap analysis tool."""

    @mcp.tool()
    def analyze_overnight_gaps(
        symbol: str,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        min_gap_pct: float = DEFAULT_MIN_GAP_PCT,
    ) -> str:
        """
        Analyze overnight gaps (previous close vs next open) and intraday fills.

        Args:
            symbol: Ticker symbol (e.g., AAPL).
            lookback_days: Number of recent trading days to analyze (flexible).
            min_gap_pct: Minimum absolute gap size (percent) to include.

        Returns:
            JSON string with summary markdown, aggregate metrics, and timeseries.
        """
        try:
            df = _fetch_daily(symbol, lookback_days)
            rows = _compute_gaps(df, min_gap_pct)
            metrics = _aggregate(rows)

            if not rows:
                return json.dumps({"error": f"No gaps >= {min_gap_pct}% in last {lookback_days} days"})

            latest = rows[-1]
            summary = f"""
### Overnight Gaps for {symbol.upper()}
- Lookback: {lookback_days} days | Min gap: {min_gap_pct:.2f}%
- Total gaps: {metrics['total_gaps']} | Up: {metrics['up_gaps']} | Down: {metrics['down_gaps']}
- Fill rate (all/up/down): {metrics['fill_rate_all']}% / {metrics['fill_rate_up']}% / {metrics['fill_rate_down']}%
- Avg gap: {metrics['avg_gap_pct']:.2f}% (up {metrics['avg_gap_up_pct']:.2f}%, down {metrics['avg_gap_down_pct']:.2f}%)
- Avg same-day close move: {metrics['avg_same_day_close_ret']:.2f}%
- Last gap: {latest['date']} {latest['direction']} {latest['gap_pct']:.2f}% | filled: {latest['filled']}
            """.strip()

            timeseries = rows[-MAX_SERIES:]
            payload = {
                "symbol": symbol.upper(),
                "lookback_days": lookback_days,
                "min_gap_pct": min_gap_pct,
                "metrics": metrics,
                "timeseries": timeseries,
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:  # pragma: no cover - defensive
            return json.dumps({"error": f"Overnight gap analysis failed: {exc}"})

    return mcp
