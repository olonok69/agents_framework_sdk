"""Bollinger breakout strategy analysis tool for MCP server.

Recreates the QuantConnect logic from qc_projects/main_bollinger.py using
Yahoo Finance OHLCV daily bars.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL = "SPY"
DEFAULT_PERIOD = "2y"
DEFAULT_BB_PERIOD = 20
DEFAULT_BB_STD = 2.0
DEFAULT_ATR_PERIOD = 14
DEFAULT_VOLUME_WINDOW = 20
DEFAULT_VOLUME_MULTIPLIER = 1.2
DEFAULT_WARMUP_BARS = 25
MAX_TRADES = 200


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


def _build_indicators(
    df: pd.DataFrame,
    bb_period: int,
    bb_std: float,
    atr_period: int,
    volume_window: int,
) -> pd.DataFrame:
    out = df.copy()
    out["mid_band"] = out["Close"].rolling(bb_period).mean()
    out["band_std"] = out["Close"].rolling(bb_period).std(ddof=0)
    out["upper_band"] = out["mid_band"] + bb_std * out["band_std"]
    out["lower_band"] = out["mid_band"] - bb_std * out["band_std"]

    out["prev_close"] = out["Close"].shift(1)
    out["tr1"] = out["High"] - out["Low"]
    out["tr2"] = (out["High"] - out["prev_close"]).abs()
    out["tr3"] = (out["Low"] - out["prev_close"]).abs()
    out["true_range"] = out[["tr1", "tr2", "tr3"]].max(axis=1)
    out["atr"] = out["true_range"].rolling(atr_period).mean()

    out["volume_sma"] = out["Volume"].rolling(volume_window).mean()
    out["volume_ratio"] = out["Volume"] / out["volume_sma"]
    return out


def _simulate(
    df: pd.DataFrame,
    warmup_bars: int,
    volume_multiplier: float,
) -> tuple[List[Dict], List[Dict]]:
    trades: List[Dict] = []
    signals: List[Dict] = []
    position = None

    ready = df.dropna(subset=["upper_band", "mid_band", "lower_band", "atr", "volume_ratio"]).copy()
    ready = ready.assign(bar_index=range(len(ready)))

    for i, (as_of, row) in enumerate(ready.iterrows()):
        if i < warmup_bars:
            continue

        price = float(row["Close"])
        upper = float(row["upper_band"])
        middle = float(row["mid_band"])
        lower = float(row["lower_band"])
        atr_val = float(row["atr"])
        vol_ratio = float(row["volume_ratio"])
        volume_confirmed = vol_ratio > volume_multiplier

        if position is None:
            if price > upper and volume_confirmed:
                size = min(0.95, (2.0 / atr_val) * 0.1) if atr_val > 0 else 0.5
                position = {
                    "entry_index": i,
                    "entry_date": as_of,
                    "entry_price": price,
                    "size": size,
                    "volume_ratio": vol_ratio,
                }
                signals.append(
                    {
                        "date": as_of.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "price": round(price, 2),
                        "upper_band": round(upper, 2),
                        "volume_ratio": round(vol_ratio, 2),
                        "position_size": round(size, 4),
                    }
                )
        else:
            if price <= lower or price <= middle:
                ret_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                trades.append(
                    {
                        "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                        "exit_date": as_of.strftime("%Y-%m-%d"),
                        "entry_price": round(position["entry_price"], 2),
                        "exit_price": round(price, 2),
                        "return_pct": round(ret_pct, 2),
                        "bars_held": i - position["entry_index"],
                        "position_size": round(position["size"], 4),
                        "entry_volume_ratio": round(position["volume_ratio"], 2),
                    }
                )
                signals.append(
                    {
                        "date": as_of.strftime("%Y-%m-%d"),
                        "type": "exit",
                        "price": round(price, 2),
                        "middle_band": round(middle, 2),
                        "lower_band": round(lower, 2),
                    }
                )
                position = None

    if position is not None and not ready.empty:
        last_date = ready.index[-1]
        last_price = float(ready.iloc[-1]["Close"])
        ret_pct = (last_price - position["entry_price"]) / position["entry_price"] * 100
        trades.append(
            {
                "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": last_date.strftime("%Y-%m-%d"),
                "entry_price": round(position["entry_price"], 2),
                "exit_price": round(last_price, 2),
                "return_pct": round(ret_pct, 2),
                "bars_held": len(ready) - position["entry_index"],
                "position_size": round(position["size"], 4),
                "entry_volume_ratio": round(position["volume_ratio"], 2),
                "forced_exit": True,
            }
        )

    return trades, signals


def _metrics(trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "avg_bars_held": 0.0,
        }

    returns = [float(t["return_pct"]) for t in trades]
    bars = [int(t["bars_held"]) for t in trades]
    return {
        "trades": len(trades),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1),
        "avg_return_pct": round(float(np.mean(returns)), 2),
        "median_return_pct": round(float(np.median(returns)), 2),
        "best_trade_pct": round(float(max(returns)), 2),
        "worst_trade_pct": round(float(min(returns)), 2),
        "avg_bars_held": round(float(np.mean(bars)), 1),
    }


def register_bollinger_breakout_tools(mcp):
    @mcp.tool()
    def analyze_bollinger_breakout(
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        bb_period: int = DEFAULT_BB_PERIOD,
        bb_std: float = DEFAULT_BB_STD,
        atr_period: int = DEFAULT_ATR_PERIOD,
        volume_window: int = DEFAULT_VOLUME_WINDOW,
        volume_multiplier: float = DEFAULT_VOLUME_MULTIPLIER,
        warmup_bars: int = DEFAULT_WARMUP_BARS,
    ) -> str:
        """Analyze Bollinger breakout strategy with QC-aligned logic.

        Entry: close > upper band and volume > volume_multiplier * volume_sma.
        Exit: close <= lower band or close <= middle band.
        Position sizing: min(95%, (2/ATR)*0.1).
        """
        try:
            frame = _download_daily(symbol.upper(), period)
            features = _build_indicators(frame, bb_period, bb_std, atr_period, volume_window)
            trades, signals = _simulate(features, warmup_bars=warmup_bars, volume_multiplier=volume_multiplier)
            stats = _metrics(trades)

            summary = (
                f"### Bollinger Breakout Overview ({symbol.upper()})\n"
                f"- Period: {period} | BB: {bb_period}/{bb_std}σ | ATR: {atr_period} | Vol SMA: {volume_window}\n"
                f"- Volume confirmation: > {volume_multiplier:.2f}x avg | Warmup: {warmup_bars} bars\n"
                f"- Trades: {stats['trades']} | Win rate: {stats['win_rate_pct']:.1f}% | Avg return: {stats['avg_return_pct']:+.2f}%\n"
                f"- Median return: {stats['median_return_pct']:+.2f}% | Best/Worst: {stats['best_trade_pct']:+.2f}% / {stats['worst_trade_pct']:+.2f}%\n"
                f"- Avg bars held: {stats['avg_bars_held']:.1f}"
            )

            payload = {
                "symbol": symbol.upper(),
                "period": period,
                "parameters": {
                    "bb_period": bb_period,
                    "bb_std": bb_std,
                    "atr_period": atr_period,
                    "volume_window": volume_window,
                    "volume_multiplier": volume_multiplier,
                    "warmup_bars": warmup_bars,
                },
                "metrics": stats,
                "trades": trades[-MAX_TRADES:],
                "signals": signals[-MAX_TRADES:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Bollinger breakout analysis failed: {exc}"})

    return mcp
