"""Volatility regime switch strategy tool for MCP server.

Approximation of qc_projects/main_volatility_regime.py using rolling SPY volatility.
"""
from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_SPY_SYMBOL = "SPY"
DEFAULT_QQQ_SYMBOL = "QQQ"
DEFAULT_ARKK_SYMBOL = "ARKK"
DEFAULT_TLT_SYMBOL = "TLT"
DEFAULT_GLD_SYMBOL = "GLD"
DEFAULT_PERIOD = "2y"
DEFAULT_VOL_WINDOW = 20
DEFAULT_HIGH_VOL_THRESHOLD = 25.0
DEFAULT_LOW_VOL_THRESHOLD = 15.0
DEFAULT_WARMUP_PERIOD = 25
MAX_EVENTS = 400


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


def _build_features(
    spy_symbol: str,
    qqq_symbol: str,
    arkk_symbol: str,
    tlt_symbol: str,
    gld_symbol: str,
    period: str,
    vol_window: int,
    warmup_period: int,
) -> pd.DataFrame:
    spy = _download_daily(spy_symbol, period)
    qqq = _download_daily(qqq_symbol, period)
    arkk = _download_daily(arkk_symbol, period)
    tlt = _download_daily(tlt_symbol, period)
    gld = _download_daily(gld_symbol, period)

    out = pd.DataFrame(index=spy.index.union(qqq.index).union(arkk.index).union(tlt.index).union(gld.index).sort_values())
    out["spy_close"] = spy["Close"]
    out["qqq_close"] = qqq["Close"]
    out["arkk_close"] = arkk["Close"]
    out["tlt_close"] = tlt["Close"]
    out["gld_close"] = gld["Close"]
    out = out.dropna().copy()

    out["spy_returns"] = out["spy_close"].pct_change()
    out["market_vol"] = out["spy_returns"].rolling(vol_window).std(ddof=0) * np.sqrt(252) * 100
    out = out.dropna(subset=["market_vol"]).copy()

    out["ret_qqq"] = out["qqq_close"].pct_change().fillna(0.0)
    out["ret_arkk"] = out["arkk_close"].pct_change().fillna(0.0)
    out["ret_tlt"] = out["tlt_close"].pct_change().fillna(0.0)
    out["ret_gld"] = out["gld_close"].pct_change().fillna(0.0)

    if warmup_period > 0 and len(out) > warmup_period:
        out = out.iloc[warmup_period:].copy()

    return out


def _simulate(
    features: pd.DataFrame,
    high_vol_threshold: float,
    low_vol_threshold: float,
) -> tuple[List[Dict], List[Dict], Dict]:
    regime_events: List[Dict] = []
    weights_history: List[Dict] = []
    current_regime = None

    portfolio_returns = []
    current_weights = {"qqq": 0.0, "arkk": 0.0, "tlt": 0.0, "gld": 0.0, "cash": 1.0}

    for ts, row in features.iterrows():
        market_vol = float(row["market_vol"])

        if market_vol > high_vol_threshold:
            new_regime = "high"
            target_weights = {"qqq": 0.0, "arkk": 0.0, "tlt": 0.5, "gld": 0.4, "cash": 0.1}
        elif market_vol < low_vol_threshold:
            new_regime = "low"
            target_weights = {"qqq": 0.6, "arkk": 0.3, "tlt": 0.0, "gld": 0.0, "cash": 0.1}
        else:
            new_regime = "medium"
            target_weights = {"qqq": 0.3, "arkk": 0.0, "tlt": 0.3, "gld": 0.2, "cash": 0.2}

        if new_regime != current_regime:
            regime_events.append(
                {
                    "timestamp": ts.strftime("%Y-%m-%d"),
                    "type": "regime_change",
                    "regime": new_regime,
                    "market_vol": round(market_vol, 3),
                    "weights": target_weights,
                }
            )
            current_regime = new_regime
            current_weights = target_weights

        daily_port_ret = (
            current_weights["qqq"] * float(row["ret_qqq"])
            + current_weights["arkk"] * float(row["ret_arkk"])
            + current_weights["tlt"] * float(row["ret_tlt"])
            + current_weights["gld"] * float(row["ret_gld"])
        )
        portfolio_returns.append(daily_port_ret)

        weights_history.append(
            {
                "timestamp": ts.strftime("%Y-%m-%d"),
                "regime": current_regime,
                "market_vol": round(market_vol, 3),
                **current_weights,
                "daily_return": round(daily_port_ret * 100, 4),
            }
        )

    return regime_events, weights_history, {"portfolio_returns": portfolio_returns}


def _metrics(features: pd.DataFrame, regime_events: List[Dict], sim_state: Dict) -> Dict:
    returns = np.array(sim_state.get("portfolio_returns", []), dtype=float)
    if returns.size == 0:
        return {
            "regime_changes": len(regime_events),
            "total_return_pct": 0.0,
            "annualized_return_pct": 0.0,
            "annualized_vol_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_market_vol": round(float(features["market_vol"].mean()), 3),
        }

    equity = np.cumprod(1.0 + returns)
    total_return = equity[-1] - 1.0
    years = max(len(returns) / 252.0, 1e-9)
    annualized_return = equity[-1] ** (1.0 / years) - 1.0
    annualized_vol = float(np.std(returns, ddof=0) * np.sqrt(252))
    sharpe = annualized_return / annualized_vol if annualized_vol > 0 else 0.0
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    max_drawdown = float(drawdown.min()) if drawdown.size > 0 else 0.0

    return {
        "regime_changes": len(regime_events),
        "total_return_pct": round(float(total_return) * 100, 3),
        "annualized_return_pct": round(float(annualized_return) * 100, 3),
        "annualized_vol_pct": round(float(annualized_vol) * 100, 3),
        "sharpe": round(float(sharpe), 3),
        "max_drawdown_pct": round(float(max_drawdown) * 100, 3),
        "avg_market_vol": round(float(features["market_vol"].mean()), 3),
        "min_market_vol": round(float(features["market_vol"].min()), 3),
        "max_market_vol": round(float(features["market_vol"].max()), 3),
    }


def register_volatility_regime_tools(mcp):
    @mcp.tool()
    def analyze_volatility_regime(
        period: str = DEFAULT_PERIOD,
        spy_symbol: str = DEFAULT_SPY_SYMBOL,
        qqq_symbol: str = DEFAULT_QQQ_SYMBOL,
        arkk_symbol: str = DEFAULT_ARKK_SYMBOL,
        tlt_symbol: str = DEFAULT_TLT_SYMBOL,
        gld_symbol: str = DEFAULT_GLD_SYMBOL,
        vol_window: int = DEFAULT_VOL_WINDOW,
        high_vol_threshold: float = DEFAULT_HIGH_VOL_THRESHOLD,
        low_vol_threshold: float = DEFAULT_LOW_VOL_THRESHOLD,
        warmup_period: int = DEFAULT_WARMUP_PERIOD,
    ) -> str:
        """Analyze volatility-regime allocation strategy using SPY rolling volatility."""
        try:
            features = _build_features(
                spy_symbol.upper().strip(),
                qqq_symbol.upper().strip(),
                arkk_symbol.upper().strip(),
                tlt_symbol.upper().strip(),
                gld_symbol.upper().strip(),
                period,
                vol_window,
                warmup_period,
            )
            regime_events, weights_history, sim_state = _simulate(features, high_vol_threshold, low_vol_threshold)
            stats = _metrics(features, regime_events, sim_state)

            summary = (
                "### Volatility Regime Overview\n"
                f"- Period: {period} | Vol window: {vol_window}\n"
                f"- Thresholds: low < {low_vol_threshold:.1f}% | high > {high_vol_threshold:.1f}%\n"
                f"- Regime changes: {stats['regime_changes']} | Avg market vol: {stats['avg_market_vol']:.3f}%\n"
                f"- Total return: {stats['total_return_pct']:+.3f}% | Annualized return: {stats['annualized_return_pct']:+.3f}%\n"
                f"- Annualized vol: {stats['annualized_vol_pct']:.3f}% | Sharpe: {stats['sharpe']:.3f} | Max drawdown: {stats['max_drawdown_pct']:.3f}%"
            )

            payload = {
                "period": period,
                "symbols": {
                    "spy": spy_symbol.upper().strip(),
                    "qqq": qqq_symbol.upper().strip(),
                    "arkk": arkk_symbol.upper().strip(),
                    "tlt": tlt_symbol.upper().strip(),
                    "gld": gld_symbol.upper().strip(),
                },
                "parameters": {
                    "vol_window": vol_window,
                    "high_vol_threshold": high_vol_threshold,
                    "low_vol_threshold": low_vol_threshold,
                    "warmup_period": warmup_period,
                },
                "metrics": stats,
                "regime_events": regime_events[-MAX_EVENTS:],
                "weights_history": weights_history[-MAX_EVENTS:],
            }
            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:
            return json.dumps({"error": f"Volatility regime analysis failed: {exc}"})

    return mcp
