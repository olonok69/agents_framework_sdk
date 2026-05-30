"""Bollinger Z-Score + RSI strategy analysis tool for MCP server.

Implements a backtest-oriented mean-reversion strategy:
- Entry: z-score <= buy threshold and RSI <= oversold threshold
- Exit: z-score >= sell threshold and RSI >= overbought threshold
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOL = "AAPL"
DEFAULT_PERIOD = "2y"
DEFAULT_BB_WINDOW = 20
DEFAULT_BB_STD = 2.0
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERSOLD = 30.0
DEFAULT_RSI_OVERBOUGHT = 70.0
DEFAULT_ZSCORE_BUY = -2.0
DEFAULT_ZSCORE_SELL = 2.0
MAX_ROWS = 300


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


def _wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _build_features(
    df: pd.DataFrame,
    bb_window: int,
    bb_std: float,
    rsi_period: int,
) -> pd.DataFrame:
    out = df.copy()
    out["bb_mean"] = out["Close"].rolling(bb_window).mean()
    out["bb_sigma"] = out["Close"].rolling(bb_window).std(ddof=0)
    out["bb_upper"] = out["bb_mean"] + bb_std * out["bb_sigma"]
    out["bb_lower"] = out["bb_mean"] - bb_std * out["bb_sigma"]
    out["zscore"] = (out["Close"] - out["bb_mean"]) / out["bb_sigma"]
    out["rsi"] = _wilder_rsi(out["Close"], rsi_period)
    return out


def _simulate(
    features: pd.DataFrame,
    rsi_oversold: float,
    rsi_overbought: float,
    zscore_buy_threshold: float,
    zscore_sell_threshold: float,
) -> tuple[List[Dict], List[Dict]]:
    trades: List[Dict] = []
    signals: List[Dict] = []
    position = None

    ready = features.dropna(subset=["bb_mean", "bb_sigma", "zscore", "rsi"]).copy()

    for as_of, row in ready.iterrows():
        price = float(row["Close"])
        z_val = float(row["zscore"])
        rsi_val = float(row["rsi"])

        if position is None:
            if z_val <= zscore_buy_threshold and rsi_val <= rsi_oversold:
                position = {
                    "entry_date": as_of,
                    "entry_price": price,
                    "entry_zscore": z_val,
                    "entry_rsi": rsi_val,
                }
                signals.append(
                    {
                        "date": as_of.strftime("%Y-%m-%d"),
                        "type": "entry",
                        "price": round(price, 2),
                        "zscore": round(z_val, 3),
                        "rsi": round(rsi_val, 2),
                    }
                )
        else:
            if z_val >= zscore_sell_threshold and rsi_val >= rsi_overbought:
                entry_date = pd.Timestamp(position["entry_date"])
                ret_pct = ((price - float(position["entry_price"])) / float(position["entry_price"])) * 100
                trades.append(
                    {
                        "entry_date": entry_date.strftime("%Y-%m-%d"),
                        "exit_date": as_of.strftime("%Y-%m-%d"),
                        "entry_price": round(float(position["entry_price"]), 2),
                        "exit_price": round(price, 2),
                        "entry_zscore": round(float(position["entry_zscore"]), 3),
                        "entry_rsi": round(float(position["entry_rsi"]), 2),
                        "exit_zscore": round(z_val, 3),
                        "exit_rsi": round(rsi_val, 2),
                        "return_pct": round(ret_pct, 2),
                        "holding_days": int((as_of - entry_date).days),
                        "exit_reason": "zscore_rsi_overbought",
                    }
                )
                signals.append(
                    {
                        "date": as_of.strftime("%Y-%m-%d"),
                        "type": "exit",
                        "price": round(price, 2),
                        "zscore": round(z_val, 3),
                        "rsi": round(rsi_val, 2),
                        "reason": "zscore_rsi_overbought",
                    }
                )
                position = None

    if position is not None and not ready.empty:
        last_date = ready.index[-1]
        last_price = float(ready.iloc[-1]["Close"])
        entry_date = pd.Timestamp(position["entry_date"])
        ret_pct = ((last_price - float(position["entry_price"])) / float(position["entry_price"])) * 100
        trades.append(
            {
                "entry_date": entry_date.strftime("%Y-%m-%d"),
                "exit_date": pd.Timestamp(last_date).strftime("%Y-%m-%d"),
                "entry_price": round(float(position["entry_price"]), 2),
                "exit_price": round(last_price, 2),
                "entry_zscore": round(float(position["entry_zscore"]), 3),
                "entry_rsi": round(float(position["entry_rsi"]), 2),
                "exit_zscore": round(float(ready.iloc[-1]["zscore"]), 3),
                "exit_rsi": round(float(ready.iloc[-1]["rsi"]), 2),
                "return_pct": round(ret_pct, 2),
                "holding_days": int((pd.Timestamp(last_date) - entry_date).days),
                "exit_reason": "forced_end_of_data",
            }
        )

    return trades, signals


def _metrics(trades: List[Dict], close: pd.Series) -> Dict:
    if close.empty:
        buy_hold_return_pct = 0.0
    else:
        buy_hold_return_pct = ((float(close.iloc[-1]) / float(close.iloc[0])) - 1.0) * 100

    if not trades:
        return {
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "avg_holding_days": 0.0,
            "strategy_return_pct": 0.0,
            "buy_hold_return_pct": round(buy_hold_return_pct, 2),
            "excess_return_pct": round(-buy_hold_return_pct, 2),
        }

    returns = np.array([float(t["return_pct"]) for t in trades], dtype=float)
    holding_days = np.array([int(t["holding_days"]) for t in trades], dtype=float)
    strategy_equity = np.prod(1.0 + (returns / 100.0)) - 1.0
    strategy_return_pct = strategy_equity * 100.0

    return {
        "total_trades": int(len(trades)),
        "win_rate_pct": round(float((returns > 0).mean() * 100), 1),
        "avg_return_pct": round(float(np.mean(returns)), 2),
        "median_return_pct": round(float(np.median(returns)), 2),
        "best_trade_pct": round(float(np.max(returns)), 2),
        "worst_trade_pct": round(float(np.min(returns)), 2),
        "avg_holding_days": round(float(np.mean(holding_days)), 1),
        "strategy_return_pct": round(float(strategy_return_pct), 2),
        "buy_hold_return_pct": round(float(buy_hold_return_pct), 2),
        "excess_return_pct": round(float(strategy_return_pct - buy_hold_return_pct), 2),
    }


def register_bollinger_zscore_rsi_tools(mcp):
    @mcp.tool()
    def analyze_bollinger_zscore_rsi_strategy(
        symbol: str = DEFAULT_SYMBOL,
        period: str = DEFAULT_PERIOD,
        bb_window: int = DEFAULT_BB_WINDOW,
        bb_std: float = DEFAULT_BB_STD,
        rsi_period: int = DEFAULT_RSI_PERIOD,
        rsi_oversold: float = DEFAULT_RSI_OVERSOLD,
        rsi_overbought: float = DEFAULT_RSI_OVERBOUGHT,
        zscore_buy_threshold: float = DEFAULT_ZSCORE_BUY,
        zscore_sell_threshold: float = DEFAULT_ZSCORE_SELL,
    ) -> str:
        """Analyze Bollinger Z-Score + RSI mean-reversion strategy.

        Entry: z-score <= zscore_buy_threshold and RSI <= rsi_oversold.
        Exit: z-score >= zscore_sell_threshold and RSI >= rsi_overbought.
        """
        try:
            ticker = symbol.upper().strip()
            frame = _download_daily(ticker, period)
            features = _build_features(frame, bb_window=bb_window, bb_std=bb_std, rsi_period=rsi_period)
            trades, signals = _simulate(
                features,
                rsi_oversold=rsi_oversold,
                rsi_overbought=rsi_overbought,
                zscore_buy_threshold=zscore_buy_threshold,
                zscore_sell_threshold=zscore_sell_threshold,
            )
            stats = _metrics(trades, features["Close"]) 

            latest = features.dropna(subset=["zscore", "rsi"]).iloc[-1]
            latest_z = float(latest["zscore"])
            latest_rsi = float(latest["rsi"])
            latest_price = float(latest["Close"])

            if latest_z <= zscore_buy_threshold and latest_rsi <= rsi_oversold:
                current_signal = "BUY"
            elif latest_z >= zscore_sell_threshold and latest_rsi >= rsi_overbought:
                current_signal = "SELL"
            else:
                current_signal = "HOLD"

            summary = (
                f"### Bollinger Z-Score + RSI Strategy ({ticker})\n"
                f"- Period: {period} | BB: {bb_window}/{bb_std}σ | RSI: {rsi_period}\n"
                f"- Entry: z <= {zscore_buy_threshold:.2f} and RSI <= {rsi_oversold:.1f}\n"
                f"- Exit: z >= {zscore_sell_threshold:.2f} and RSI >= {rsi_overbought:.1f}\n"
                f"- Current: price={latest_price:.2f}, z={latest_z:.3f}, rsi={latest_rsi:.2f}, signal={current_signal}\n"
                f"- Trades: {stats['total_trades']} | Win rate: {stats['win_rate_pct']:.1f}% | Avg return: {stats['avg_return_pct']:+.2f}%\n"
                f"- Strategy vs Buy&Hold: {stats['strategy_return_pct']:+.2f}% vs {stats['buy_hold_return_pct']:+.2f}% "
                f"(excess {stats['excess_return_pct']:+.2f}%)"
            )

            payload = {
                "symbol": ticker,
                "period": period,
                "parameters": {
                    "bb_window": bb_window,
                    "bb_std": bb_std,
                    "rsi_period": rsi_period,
                    "rsi_oversold": rsi_oversold,
                    "rsi_overbought": rsi_overbought,
                    "zscore_buy_threshold": zscore_buy_threshold,
                    "zscore_sell_threshold": zscore_sell_threshold,
                },
                "metrics": stats,
                "latest": {
                    "price": round(latest_price, 2),
                    "zscore": round(latest_z, 3),
                    "rsi": round(latest_rsi, 2),
                    "signal": current_signal,
                },
                "trades": trades[-MAX_ROWS:],
                "signals": signals[-MAX_ROWS:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Bollinger Z-Score RSI strategy analysis failed: {exc}"})

    return mcp
