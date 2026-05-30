"""
Earnings momentum strategy based on volume-surged post-earnings reactions.

This MCP tool scans a list of symbols, looks for sessions where volume
exceeds a moving average multiple plus bullish closes, and simulates
holding those positions for a fixed number of bars.
"""
from __future__ import annotations

import json
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
]
DEFAULT_PERIOD = "6mo"
DEFAULT_VOLUME_WINDOW = 20
DEFAULT_VOLUME_MULTIPLIER = 2.0
DEFAULT_HOLD_DAYS = 5
DEFAULT_MAX_POSITIONS = 3
MAX_SIGNALS = 200
MAX_TRADES = 200


def _normalize_symbols(symbols: str | Sequence[str] | None) -> List[str]:
    if symbols is None:
        return list(DEFAULT_SYMBOLS)
    if isinstance(symbols, str):
        parts = [part.strip().upper() for part in symbols.split(",")]
    else:
        parts = [str(part).strip().upper() for part in symbols]
    cleaned = [part for part in parts if part]
    return cleaned or list(DEFAULT_SYMBOLS)


def _download_history(symbol: str, period: str) -> pd.DataFrame:
    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        progress=False,
        multi_level_index=False,
    )
    if data is None or data.empty:
        raise ValueError(f"No OHLCV data for {symbol}")
    frame = data[["Open", "High", "Low", "Close", "Volume"]].dropna()
    frame = frame.reset_index().rename(columns={"Date": "date"})
    frame["symbol"] = symbol
    return frame


def _build_universe(
    symbols: List[str],
    period: str,
    volume_window: int,
) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    missing: List[str] = []
    for symbol in symbols:
        try:
            frames.append(_download_history(symbol, period))
        except Exception:
            missing.append(symbol)
            continue

    if not frames:
        raise ValueError("Unable to download price/volume data for requested symbols")

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"])
    combined.sort_values(["date", "symbol"], inplace=True)
    combined["volume_sma"] = combined.groupby("symbol")["Volume"].transform(
        lambda s: s.rolling(volume_window).mean()
    )
    combined["volume_ratio"] = combined["Volume"] / combined["volume_sma"]
    combined["bullish_close"] = combined["Close"] > combined["Open"]
    combined["missing"] = False

    if missing:
        missing_frame = pd.DataFrame({
            "symbol": missing,
            "date": pd.NaT,
            "Volume": np.nan,
            "Open": np.nan,
            "Close": np.nan,
            "volume_sma": np.nan,
            "volume_ratio": np.nan,
            "bullish_close": False,
            "missing": True,
        })
        combined = pd.concat([combined, missing_frame], ignore_index=True, sort=False)

    return combined


def _simulate_strategy(
    data: pd.DataFrame,
    hold_days: int,
    max_positions: int,
    volume_multiplier: float,
) -> tuple[List[dict], List[dict]]:
    active_positions: Dict[str, Dict] = {}
    trades: List[dict] = []
    signals: List[dict] = []

    grouped = data.dropna(subset=["date"]).groupby("date", sort=True)
    for trade_date, daily_frame in grouped:
        daily_records = daily_frame.to_dict("records")
        record_map = {rec["symbol"]: rec for rec in daily_records}

        # Update and close existing positions
        symbols_in_position = list(active_positions.keys())
        for symbol in symbols_in_position:
            pos = active_positions[symbol]
            if symbol not in record_map:
                continue
            pos["bars_held"] += 1
            if pos["bars_held"] >= hold_days:
                exit_row = record_map[symbol]
                exit_price = float(exit_row["Close"])
                ret_pct = (exit_price - pos["entry_price"]) / pos["entry_price"] * 100
                trades.append({
                    "symbol": symbol,
                    "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": trade_date.strftime("%Y-%m-%d"),
                    "entry_price": round(pos["entry_price"], 4),
                    "exit_price": round(exit_price, 4),
                    "return_pct": round(ret_pct, 2),
                    "volume_ratio": round(pos["volume_ratio"], 2),
                    "hold_days": pos["bars_held"],
                })
                del active_positions[symbol]

        # Evaluate new entries prioritizing strongest volume spikes
        available_slots = max_positions - len(active_positions)
        if available_slots <= 0:
            continue

        candidates = [
            rec
            for rec in daily_records
            if rec.get("bullish_close")
            and rec.get("symbol") not in active_positions
            and np.isfinite(rec.get("volume_ratio", np.nan))
            and rec.get("volume_ratio", 0) >= volume_multiplier
        ]
        if not candidates:
            continue

        candidates.sort(key=lambda rec: rec["volume_ratio"], reverse=True)
        for rec in candidates[:available_slots]:
            symbol = rec["symbol"]
            entry_price = float(rec["Close"])
            active_positions[symbol] = {
                "entry_date": rec["date"],
                "entry_price": entry_price,
                "volume_ratio": float(rec["volume_ratio"]),
                "bars_held": 0,
            }
            signals.append({
                "date": rec["date"].strftime("%Y-%m-%d"),
                "symbol": symbol,
                "volume_ratio": round(float(rec["volume_ratio"]), 2),
                "close": round(entry_price, 2),
                "note": "Volume spike + bullish session",
            })

    # Force close any remaining positions at their latest available bar
    if active_positions:
        for symbol, pos in list(active_positions.items()):
            symbol_history = (
                data[data["symbol"] == symbol]
                .sort_values("date")
                .dropna(subset=["Close"])
            )
            if symbol_history.empty:
                continue
            last_row = symbol_history.iloc[-1]
            exit_price = float(last_row["Close"])
            ret_pct = (exit_price - pos["entry_price"]) / pos["entry_price"] * 100
            trades.append({
                "symbol": symbol,
                "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": last_row["date"].strftime("%Y-%m-%d"),
                "entry_price": round(pos["entry_price"], 4),
                "exit_price": round(exit_price, 4),
                "return_pct": round(ret_pct, 2),
                "volume_ratio": round(pos["volume_ratio"], 2),
                "hold_days": hold_days,
                "forced_exit": True,
            })
            del active_positions[symbol]

    return trades, signals


def _aggregate(trades: List[dict], signals: List[dict], symbols: List[str]) -> Dict[str, Dict]:
    per_symbol: Dict[str, Dict] = {}
    for symbol in symbols:
        symbol_trades = [trade for trade in trades if trade.get("symbol") == symbol]
        if not symbol_trades:
            continue
        returns = [trade["return_pct"] for trade in symbol_trades]
        per_symbol[symbol] = {
            "trades": len(symbol_trades),
            "win_rate_pct": round(
                sum(1 for val in returns if val > 0) / len(symbol_trades) * 100, 1
            ) if symbol_trades else 0.0,
            "avg_return_pct": round(float(np.mean(returns)), 2),
            "median_return_pct": round(float(np.median(returns)), 2),
            "best_trade_pct": round(max(returns), 2),
            "worst_trade_pct": round(min(returns), 2),
        }
    return per_symbol


def _build_summary(
    symbols: List[str],
    period: str,
    trades: List[dict],
    signals: List[dict],
    per_symbol: Dict[str, Dict],
    volume_window: int,
    hold_days: int,
    volume_multiplier: float,
    max_positions: int,
) -> tuple[str, Dict]:
    aggregate: Dict[str, float] = {
        "total_trades": len(trades),
        "win_rate_pct": round(
            sum(1 for trade in trades if trade["return_pct"] > 0) / len(trades) * 100,
            1,
        ) if trades else 0.0,
        "avg_return_pct": round(float(np.mean([t["return_pct"] for t in trades])), 2)
        if trades
        else 0.0,
        "median_return_pct": round(
            float(np.median([t["return_pct"] for t in trades])), 2
        ) if trades else 0.0,
        "avg_hold_days": round(
            float(np.mean([t["hold_days"] for t in trades])), 1
        ) if trades else float(hold_days),
    }

    leaders = sorted(
        (
            (symbol, stats)
            for symbol, stats in per_symbol.items()
            if stats.get("trades")
        ),
        key=lambda item: (item[1]["avg_return_pct"], item[1]["win_rate_pct"], item[1]["trades"]),
        reverse=True,
    )[:3]
    leader_text = ", ".join(
        f"{symbol} ({stats['avg_return_pct']:+.2f}% avg)" for symbol, stats in leaders
    ) or "No leaders yet"
    recent = signals[-3:]
    recent_text = "; ".join(
        f"{sig['date']} {sig['symbol']} {sig['volume_ratio']:.1f}×" for sig in recent
    ) or "No recent entries"

    summary = f"""
### Earnings Momentum Overview
- Universe: {', '.join(symbols)} | Period: {period}
- Params: vol window {volume_window}d | spike ≥ {volume_multiplier:.1f}× | Hold {hold_days} bars | Max {max_positions} positions
- Trades: {aggregate['total_trades']} | Win rate: {aggregate['win_rate_pct']:.1f}% | Avg return: {aggregate['avg_return_pct']:+.2f}%
- Leaders: {leader_text}
- Recent entries: {recent_text}
""".strip()

    payload = {
        "symbols": symbols,
        "aggregate": aggregate,
        "per_symbol": per_symbol,
        "recent_signals": recent,
        "leaders": leaders,
    }
    return summary, payload


def register_earnings_momentum_tools(mcp):
    """Register the earnings momentum strategy tool with FastMCP."""

    @mcp.tool()
    def analyze_earnings_momentum(
        symbols: str = ",".join(DEFAULT_SYMBOLS),
        period: str = DEFAULT_PERIOD,
        volume_window: int = DEFAULT_VOLUME_WINDOW,
        volume_multiplier: float = DEFAULT_VOLUME_MULTIPLIER,
        hold_days: int = DEFAULT_HOLD_DAYS,
        max_positions: int = DEFAULT_MAX_POSITIONS,
    ) -> str:
        """Scan a basket of symbols for post-earnings momentum bursts.

        Args:
            symbols: Comma-separated list of tickers to monitor.
            period: Historical window (e.g., 3mo, 6mo, 1y).
            volume_window: Rolling window for average volume.
            volume_multiplier: Threshold for declaring a volume spike.
            hold_days: Number of trading bars to hold each position.
            max_positions: Maximum concurrent positions across symbols.

        Returns:
            JSON string containing summary markdown, aggregate stats, and trades/signals.
        """

        if hold_days < 1:
            raise ValueError("hold_days must be >= 1")
        if max_positions < 1:
            raise ValueError("max_positions must be >= 1")
        if volume_window < 5:
            raise ValueError("volume_window must be >= 5")

        symbol_list = _normalize_symbols(symbols)
        try:
            universe = _build_universe(symbol_list, period, volume_window)
            filtered_universe = universe[~universe["missing"]].copy()
            trades, signals = _simulate_strategy(
                filtered_universe,
                hold_days=hold_days,
                max_positions=max_positions,
                volume_multiplier=volume_multiplier,
            )
            per_symbol = _aggregate(trades, signals, symbol_list)
            summary, aggregate_payload = _build_summary(
                symbol_list,
                period,
                trades,
                signals,
                per_symbol,
                volume_window,
                hold_days,
                volume_multiplier,
                max_positions,
            )

            payload = {
                "summary": summary,
                "metrics": {
                    "parameters": {
                        "symbols": symbol_list,
                        "period": period,
                        "volume_window": volume_window,
                        "volume_multiplier": volume_multiplier,
                        "hold_days": hold_days,
                        "max_positions": max_positions,
                    },
                    **aggregate_payload,
                    "trades": trades[-MAX_TRADES:],
                    "signals": signals[-MAX_SIGNALS:],
                },
            }
            return json.dumps(payload, indent=2)
        except Exception as exc:  # pragma: no cover - defensive
            return json.dumps({"error": f"Earnings momentum analysis failed: {exc}"})

    return mcp
