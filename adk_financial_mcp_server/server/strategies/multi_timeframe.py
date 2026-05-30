"""Multi-timeframe strategy analysis tool for MCP server.

Approximation of qc_projects/main_multi_timeframe.py using daily trend + hourly RSI.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL = "SPY"
DEFAULT_PERIOD = "2y"
DEFAULT_SMA_FAST = 50
DEFAULT_SMA_SLOW = 200
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERSOLD = 30
DEFAULT_RSI_EXIT = 70
DEFAULT_WARMUP_DAYS = 210
MAX_TRADES = 300


def _download_daily(symbol: str, period: str) -> pd.DataFrame:
    data = yf.download(symbol, period=period, interval="1d", progress=False, multi_level_index=False, auto_adjust=False)
    if data is None or data.empty:
        raise ValueError(f"No daily data for {symbol}")
    frame = data[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame


def _download_hourly(symbol: str, period: str) -> pd.DataFrame:
    data = yf.download(symbol, period=period, interval="60m", progress=False, multi_level_index=False, auto_adjust=False)
    if data is None or data.empty:
        raise ValueError(f"No hourly data for {symbol}")
    frame = data[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame


def _wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _build_features(
    symbol: str,
    period: str,
    sma_fast: int,
    sma_slow: int,
    rsi_period: int,
) -> pd.DataFrame:
    daily = _download_daily(symbol, period)
    hourly = _download_hourly(symbol, period)

    daily_feat = daily[["Close"]].copy()
    daily_feat["sma_fast"] = daily_feat["Close"].rolling(sma_fast).mean()
    daily_feat["sma_slow"] = daily_feat["Close"].rolling(sma_slow).mean()
    daily_feat["uptrend"] = daily_feat["sma_fast"] > daily_feat["sma_slow"]
    daily_feat.dropna(inplace=True)

    hourly_feat = hourly.copy()
    hourly_feat["rsi"] = _wilder_rsi(hourly_feat["Close"], rsi_period)
    hourly_feat["session_date"] = pd.to_datetime(hourly_feat.index).floor("D")

    trend_cols = daily_feat[["sma_fast", "sma_slow", "uptrend"]]
    merged = hourly_feat.merge(trend_cols, left_on="session_date", right_index=True, how="left")
    merged.dropna(subset=["rsi", "sma_slow"], inplace=True)
    return merged


def _simulate(
    features: pd.DataFrame,
    warmup_days: int,
    rsi_oversold: float,
    rsi_exit: float,
) -> tuple[List[Dict], List[Dict]]:
    trades: List[Dict] = []
    signals: List[Dict] = []
    position = None

    for ts, row in features.iterrows():
        uptrend = bool(row["uptrend"])
        rsi_val = float(row["rsi"])
        price = float(row["Close"])

        if position is None:
            if uptrend and rsi_val < rsi_oversold:
                position = {
                    "entry_time": ts,
                    "entry_price": price,
                    "entry_rsi": rsi_val,
                    "entry_uptrend": uptrend,
                }
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
                        "type": "entry",
                        "price": round(price, 2),
                        "rsi": round(rsi_val, 2),
                        "uptrend": uptrend,
                    }
                )
        else:
            exit_condition = (rsi_val > rsi_exit) or (not uptrend)
            if exit_condition:
                ret_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                reason = "rsi_exit" if rsi_val > rsi_exit else "trend_reversal"
                trades.append(
                    {
                        "entry_time": pd.Timestamp(position["entry_time"]).strftime("%Y-%m-%d %H:%M"),
                        "exit_time": pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M"),
                        "entry_price": round(position["entry_price"], 2),
                        "exit_price": round(price, 2),
                        "entry_rsi": round(float(position["entry_rsi"]), 2),
                        "exit_rsi": round(rsi_val, 2),
                        "return_pct": round(ret_pct, 2),
                        "exit_reason": reason,
                    }
                )
                signals.append(
                    {
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
                        "type": "exit",
                        "price": round(price, 2),
                        "rsi": round(rsi_val, 2),
                        "exit_reason": reason,
                    }
                )
                position = None

    return trades, signals


def _metrics(trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
        }

    returns = [float(t["return_pct"]) for t in trades]
    return {
        "total_trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 2),
        "median_return_pct": round(float(np.median(returns)), 2),
        "best_trade_pct": round(float(max(returns)), 2),
        "worst_trade_pct": round(float(min(returns)), 2),
    }


def register_multi_timeframe_tools(mcp):
    @mcp.tool()
    def analyze_multi_timeframe(
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        sma_fast: int = DEFAULT_SMA_FAST,
        sma_slow: int = DEFAULT_SMA_SLOW,
        rsi_period: int = DEFAULT_RSI_PERIOD,
        rsi_oversold: float = DEFAULT_RSI_OVERSOLD,
        rsi_exit: float = DEFAULT_RSI_EXIT,
        warmup_days: int = DEFAULT_WARMUP_DAYS,
    ) -> str:
        """Analyze multi-timeframe momentum strategy.

        Daily trend filter: SMA fast > SMA slow.
        Hourly entry: RSI < rsi_oversold while trend is up.
        Exit: RSI > rsi_exit or trend reversal.
        """
        try:
            features = _build_features(symbol.upper(), period, sma_fast, sma_slow, rsi_period)
            trades, signals = _simulate(features, warmup_days, rsi_oversold, rsi_exit)
            stats = _metrics(trades)

            summary = (
                f"### Multi-Timeframe Overview ({symbol.upper()})\n"
                f"- Period: {period} | SMA: {sma_fast}/{sma_slow} | RSI: {rsi_period}\n"
                f"- Entry RSI < {rsi_oversold} with uptrend | Exit RSI > {rsi_exit} or trend reversal\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}%\n"
                f"- Avg return: {stats['avg_return_pct']:+.2f}% | Median return: {stats['median_return_pct']:+.2f}%\n"
                f"- Best/Worst: {stats['best_trade_pct']:+.2f}% / {stats['worst_trade_pct']:+.2f}%"
            )

            payload = {
                "symbol": symbol.upper(),
                "period": period,
                "parameters": {
                    "sma_fast": sma_fast,
                    "sma_slow": sma_slow,
                    "rsi_period": rsi_period,
                    "rsi_oversold": rsi_oversold,
                    "rsi_exit": rsi_exit,
                    "warmup_days": warmup_days,
                },
                "metrics": stats,
                "trades": trades[-MAX_TRADES:],
                "signals": signals[-MAX_TRADES:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Multi-timeframe analysis failed: {exc}"})

    return mcp
