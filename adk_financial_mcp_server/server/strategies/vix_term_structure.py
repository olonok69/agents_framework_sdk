"""VIX term structure strategy analysis tool for MCP server.

Approximation of qc_projects/main_vix_term_structure.py using realized volatility
proxies from SPY daily returns.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL = "SPY"
DEFAULT_PERIOD = "2y"
DEFAULT_FRONT_WINDOW = 10
DEFAULT_BACK_WINDOW = 30
DEFAULT_CONTANGO_THRESHOLD = 1.05
DEFAULT_BACKWARDATION_THRESHOLD = 0.95
DEFAULT_LONG_POSITION_SIZE = 0.8
DEFAULT_SHORT_POSITION_SIZE = -0.5
DEFAULT_WARMUP_PERIOD = 35
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


def _build_features(symbol: str, period: str, front_window: int, back_window: int, warmup_period: int) -> pd.DataFrame:
    df = _download_daily(symbol, period)
    out = df.copy()
    out["returns"] = out["Close"].pct_change()
    out["front_vol"] = out["returns"].rolling(front_window).std(ddof=0) * np.sqrt(252) * 100
    out["back_vol"] = out["returns"].rolling(back_window).std(ddof=0) * np.sqrt(252) * 100
    out["term_ratio"] = out["back_vol"] / out["front_vol"]
    out["term_ratio"] = out["term_ratio"].replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["front_vol", "back_vol", "term_ratio"]).copy()

    if warmup_period > 0 and len(out) > warmup_period:
        out = out.iloc[warmup_period:].copy()

    return out


def _simulate(
    features: pd.DataFrame,
    contango_threshold: float,
    backwardation_threshold: float,
    long_position_size: float,
    short_position_size: float,
) -> tuple[List[Dict], List[Dict]]:
    position = 0
    entry_price = 0.0
    entry_time = None
    entry_ratio = None
    entry_size = 0.0

    trades: List[Dict] = []
    signals: List[Dict] = []

    for ts, row in features.iterrows():
        ratio = float(row["term_ratio"])
        price = float(row["Close"])

        if position == 0:
            if ratio < backwardation_threshold:
                position = 1
                entry_price = price
                entry_time = ts
                entry_ratio = ratio
                entry_size = long_position_size
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "side": "long",
                        "term_ratio": round(ratio, 4),
                        "price": round(price, 2),
                    }
                )
            elif ratio > contango_threshold:
                position = -1
                entry_price = price
                entry_time = ts
                entry_ratio = ratio
                entry_size = short_position_size
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "side": "short",
                        "term_ratio": round(ratio, 4),
                        "price": round(price, 2),
                    }
                )

        elif position == 1:
            if ratio > 1.0:
                raw_ret = price / entry_price - 1.0
                ret_pct = raw_ret * abs(entry_size) * 100
                trades.append(
                    {
                        "side": "long",
                        "entry_time": pd.Timestamp(entry_time).strftime("%Y-%m-%d"),
                        "exit_time": ts.strftime("%Y-%m-%d"),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(price, 2),
                        "entry_ratio": round(float(entry_ratio), 4),
                        "exit_ratio": round(ratio, 4),
                        "return_pct": round(float(ret_pct), 3),
                    }
                )
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "exit",
                        "side": "long",
                        "term_ratio": round(ratio, 4),
                        "price": round(price, 2),
                    }
                )
                position = 0

        elif position == -1:
            if ratio < 1.0:
                raw_ret = price / entry_price - 1.0
                ret_pct = (-raw_ret) * abs(entry_size) * 100
                trades.append(
                    {
                        "side": "short",
                        "entry_time": pd.Timestamp(entry_time).strftime("%Y-%m-%d"),
                        "exit_time": ts.strftime("%Y-%m-%d"),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(price, 2),
                        "entry_ratio": round(float(entry_ratio), 4),
                        "exit_ratio": round(ratio, 4),
                        "return_pct": round(float(ret_pct), 3),
                    }
                )
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d"),
                        "type": "exit",
                        "side": "short",
                        "term_ratio": round(ratio, 4),
                        "price": round(price, 2),
                    }
                )
                position = 0

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
            "avg_term_ratio": round(float(features["term_ratio"].mean()), 4),
            "min_term_ratio": round(float(features["term_ratio"].min()), 4),
            "max_term_ratio": round(float(features["term_ratio"].max()), 4),
        }

    returns = [float(t["return_pct"]) for t in trades]
    return {
        "total_trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 3),
        "median_return_pct": round(float(np.median(returns)), 3),
        "best_trade_pct": round(float(max(returns)), 3),
        "worst_trade_pct": round(float(min(returns)), 3),
        "avg_term_ratio": round(float(features["term_ratio"].mean()), 4),
        "min_term_ratio": round(float(features["term_ratio"].min()), 4),
        "max_term_ratio": round(float(features["term_ratio"].max()), 4),
    }


def register_vix_term_structure_tools(mcp):
    @mcp.tool()
    def analyze_vix_term_structure(
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        front_window: int = DEFAULT_FRONT_WINDOW,
        back_window: int = DEFAULT_BACK_WINDOW,
        contango_threshold: float = DEFAULT_CONTANGO_THRESHOLD,
        backwardation_threshold: float = DEFAULT_BACKWARDATION_THRESHOLD,
        long_position_size: float = DEFAULT_LONG_POSITION_SIZE,
        short_position_size: float = DEFAULT_SHORT_POSITION_SIZE,
        warmup_period: int = DEFAULT_WARMUP_PERIOD,
    ) -> str:
        """Analyze synthetic VIX term-structure strategy using realized-vol proxies."""
        try:
            sym = symbol.upper().strip()
            features = _build_features(sym, period, front_window, back_window, warmup_period)
            trades, signals = _simulate(
                features,
                contango_threshold,
                backwardation_threshold,
                long_position_size,
                short_position_size,
            )
            stats = _metrics(features, trades)

            summary = (
                f"### VIX Term Structure Overview ({sym})\n"
                f"- Period: {period} | Vol windows: front={front_window}, back={back_window}\n"
                f"- Entry long (backwardation): ratio < {backwardation_threshold} at size {long_position_size:+.2f}\n"
                f"- Entry short (contango): ratio > {contango_threshold} at size {short_position_size:+.2f}\n"
                f"- Exit long if ratio > 1.0 | Exit short if ratio < 1.0\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}%\n"
                f"- Avg return: {stats['avg_return_pct']:+.3f}% | Median: {stats['median_return_pct']:+.3f}%\n"
                f"- Best/Worst: {stats['best_trade_pct']:+.3f}% / {stats['worst_trade_pct']:+.3f}% | Ratio range: {stats['min_term_ratio']:.4f}..{stats['max_term_ratio']:.4f}"
            )

            payload = {
                "symbol": sym,
                "period": period,
                "parameters": {
                    "front_window": front_window,
                    "back_window": back_window,
                    "contango_threshold": contango_threshold,
                    "backwardation_threshold": backwardation_threshold,
                    "long_position_size": long_position_size,
                    "short_position_size": short_position_size,
                    "warmup_period": warmup_period,
                },
                "metrics": stats,
                "trades": trades[-MAX_TRADES:],
                "signals": signals[-MAX_TRADES:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"VIX term structure analysis failed: {exc}"})

    return mcp
