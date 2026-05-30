"""
TRIN (Arms Index) market breadth tool for MCP server.

This implements a standalone, low-level tool that fetches the NYSE TRIN
index from Yahoo Finance (ticker: ^TRIN), builds Bollinger-style bands on
log-transformed values (optional), and emits a concise signal summary.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict

from dotenv import load_dotenv

import numpy as np
import pandas as pd
import requests
import yfinance as yf

# Sensible defaults matching the legacy notebook
DEFAULT_PERIOD = "6mo"
DEFAULT_WINDOW = 20
DEFAULT_BAND_K = 1.5


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert a period string into start/end ISO dates (UTC)."""
    today = datetime.now(timezone.utc).date()
    days_map = {
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }
    days = days_map.get(period, 365)
    start = today - timedelta(days=days)
    return start.isoformat(), today.isoformat()


def _fetch_trin_series_nasdaq(api_key: str, period: str) -> pd.Series:
    """Fetch TRIN components from Nasdaq Data Link (URC datasets)."""

    def fetch_series(dataset_code: str, start: str, end: str) -> pd.Series:
        url = f"https://data.nasdaq.com/api/v3/datasets/{dataset_code}.json"
        params = {"api_key": api_key, "start_date": start, "end_date": end}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("dataset", {}).get("data", [])
        if not data:
            raise ValueError(f"Empty data for {dataset_code}")
        frame = pd.DataFrame(data, columns=["Date", "Value"]).set_index("Date")
        return pd.to_numeric(frame["Value"], errors="coerce").dropna().sort_index()

    start_date, end_date = _period_to_dates(period)
    advancing = fetch_series("URC/NYSE_ADV", start_date, end_date)
    declining = fetch_series("URC/NYSE_DEC", start_date, end_date)
    adv_vol = fetch_series("URC/NYSE_ADV_VOL", start_date, end_date)
    dec_vol = fetch_series("URC/NYSE_DEC_VOL", start_date, end_date)

    df = pd.DataFrame({
        "advancing": advancing,
        "declining": declining,
        "adv_vol": adv_vol,
        "dec_vol": dec_vol,
    }).dropna()

    if df.empty:
        raise ValueError("No overlapping TRIN component data from Nasdaq Data Link")

    trin = (df["advancing"] / df["declining"]) / (df["adv_vol"] / df["dec_vol"])
    series = pd.to_numeric(trin, errors="coerce").dropna()
    if series.empty:
        raise ValueError("Computed TRIN series is empty")
    return series


def _fetch_trin_series(period: str) -> pd.Series:
    """Download TRIN close prices with ticker and period fallbacks.

    Yahoo Finance sometimes returns empty frames for ^TRIN. We try multiple
    tickers and periods, then a long-date range as a final fallback.
    """
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("NASDAQ_DATA_LINK_API_KEY") or os.getenv("QUANDL_API_KEY")
    last_error: str | None = None

    # Try Nasdaq Data Link (preferred when key is available)
    if api_key:
        try:
            return _fetch_trin_series_nasdaq(api_key, period)
        except Exception as exc:  # pragma: no cover - defensive
            last_error = f"Nasdaq Data Link fallback failed: {exc}"

    tickers = ["^TRIN", "TRIN", "TRINQ"]
    fallback_periods = [period, "1y", "2y", "5y", "max"]

    # Try period-based downloads first
    for ticker in tickers:
        for p in fallback_periods:
            try:
                data = yf.download(ticker, period=p, interval="1d", progress=False, multi_level_index=False)
                if data is None or data.empty:
                    last_error = f"Empty data for {ticker} period {p}"
                    continue

                series = pd.to_numeric(data.get("Close"), errors="coerce").dropna()
                if series.empty:
                    last_error = f"Missing close prices for {ticker} period {p}"
                    continue

                # Validate that this looks like TRIN data (should be around 1.0, not stock prices)
                mean_value = series.mean()
                if not (0.1 <= mean_value <= 5.0):
                    last_error = f"Data for {ticker} doesn't look like TRIN (mean: {mean_value:.2f}, expected ~1.0)"
                    continue

                return series
            except Exception as exc:  # pragma: no cover - defensive
                last_error = f"Download failed for {ticker} period {p}: {exc}"
                continue

    # Final attempt: explicit start date range
    for ticker in tickers:
        try:
            data = yf.download(
                ticker,
                start="2000-01-01",
                end=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                interval="1d",
                progress=False,
                multi_level_index=False,
            )
            if data is None or data.empty:
                last_error = f"Empty data for {ticker} with explicit date range"
                continue

            series = pd.to_numeric(data.get("Close"), errors="coerce").dropna()
            if series.empty:
                last_error = f"Missing close prices for {ticker} with explicit date range"
                continue

            # Validate that this looks like TRIN data (should be around 1.0, not stock prices)
            mean_value = series.mean()
            if not (0.1 <= mean_value <= 5.0):
                last_error = f"Data for {ticker} doesn't look like TRIN (mean: {mean_value:.2f}, expected ~1.0)"
                continue

            return series
        except Exception as exc:  # pragma: no cover - defensive
            last_error = f"Download failed for {ticker} explicit range: {exc}"
            continue

    raise ValueError(last_error or "No valid TRIN data found. The TRIN (Arms Index) requires premium data access. Consider using synthetic data for demonstration purposes.")


def _build_trin_frame(series: pd.Series, window: int, band_k: float, use_log: bool) -> pd.DataFrame:
    """Prepare DataFrame with moving average and Bollinger-style bands."""
    df = pd.DataFrame(index=series.index)
    df["trin_raw"] = series

    if use_log:
        # Avoid log(0); clip to small positive
        df["trin"] = np.log(df["trin_raw"].clip(lower=1e-6))
    else:
        df["trin"] = df["trin_raw"]

    df["ma"] = df["trin"].rolling(window).mean()
    df["std"] = df["trin"].rolling(window).std()
    df["upper"] = df["ma"] + band_k * df["std"]
    df["lower"] = df["ma"] - band_k * df["std"]
    df["trend"] = df["trin"].diff().rolling(3).mean()
    return df.dropna()


def _derive_signal(row: pd.Series) -> Dict[str, str]:
    """Generate contrarian signal based on TRIN level vs bands."""
    trin_value = float(row["trin_raw"])
    band_state = "inside_band"
    signal = "neutral"
    bias = "risk_neutral"
    rationale = []

    if trin_value > 1.0:
        bias = "risk_off_pressure"
        rationale.append("TRIN above 1.0 shows elevated selling pressure")
    elif trin_value < 1.0:
        bias = "risk_on_bid"
        rationale.append("TRIN below 1.0 shows buying pressure")
    else:
        rationale.append("TRIN near 1.0 (balanced breadth)")

    if row["trin"] > row["upper"]:
        band_state = "above_upper"
        signal = "bullish_reversal_setup"
        rationale.append("Crossed above upper band — capitulation risk, contrarian bullish")
    elif row["trin"] < row["lower"]:
        band_state = "below_lower"
        signal = "bearish_reversal_setup"
        rationale.append("Crossed below lower band — euphoria risk, contrarian cautious")
    elif row["trin"] > row["ma"]:
        band_state = "between_ma_and_upper"
        signal = "caution"
        rationale.append("Above moving average — selling pressure elevated vs trend")
    else:
        band_state = "between_ma_and_lower"
        signal = "constructive"
        rationale.append("Below moving average — buying pressure dominating")

    return {
        "signal": signal,
        "band_state": band_state,
        "bias": bias,
        "rationale": "; ".join(rationale),
    }


def register_trin_strategy_tools(mcp):
    """Register TRIN breadth analysis as a low-level MCP tool."""

    @mcp.tool()
    def analyze_trin_market_breadth(
        period: str = DEFAULT_PERIOD,
        window: int = DEFAULT_WINDOW,
        band_k: float = DEFAULT_BAND_K,
        use_log: bool = True,
    ) -> str:
        """
        Analyze the TRIN (Arms Index) market breadth indicator.

        - Fetches TRIN from Yahoo Finance ticker ^TRIN
        - Builds moving average and Bollinger-style bands
        - Emits a contrarian-style signal (washout vs euphoria)

        Args:
            period: Data period (e.g., 1mo, 3mo, 6mo, 1y).
            window: Rolling window for mean/std (default 20).
            band_k: Band width in standard deviations (default 1.5).
            use_log: Apply log transform to stabilize variance (default True).

        Returns:
            JSON string with latest metrics, signal, and rationale.
        """
        try:
            series = _fetch_trin_series(period)
            frame = _build_trin_frame(series, window, band_k, use_log)
            latest = frame.iloc[-1]

            # Calculate short-term change for context
            pct_change_5d = float(series.pct_change(5).iloc[-1] * 100) if len(series) > 5 else 0.0
            signal_info = _derive_signal(latest)

            payload = {
                "as_of": frame.index[-1].strftime("%Y-%m-%d"),
                "trin": round(float(latest["trin_raw"]), 4),
                "ma": round(float(latest["ma"]), 4),
                "upper": round(float(latest["upper"]), 4),
                "lower": round(float(latest["lower"]), 4),
                "window": int(window),
                "band_k": float(band_k),
                "use_log": bool(use_log),
                "bias": signal_info["bias"],
                "signal": signal_info["signal"],
                "band_state": signal_info["band_state"],
                "rationale": signal_info["rationale"],
                "change_5d_pct": round(pct_change_5d, 2),
                "data_points": int(len(frame)),
                "note": "Contrarian read: high TRIN often precedes bullish reversals; low TRIN can mark euphoria.",
            }

            # Prepare compact time series for plotting (max 200 points)
            ts_frame = frame.tail(200).copy()
            if use_log:
                ts_frame["ma_plot"] = np.exp(ts_frame["ma"])
                ts_frame["upper_plot"] = np.exp(ts_frame["upper"])
                ts_frame["lower_plot"] = np.exp(ts_frame["lower"])
            else:
                ts_frame["ma_plot"] = ts_frame["ma"]
                ts_frame["upper_plot"] = ts_frame["upper"]
                ts_frame["lower_plot"] = ts_frame["lower"]

            timeseries = [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "trin": float(row["trin_raw"]),
                    "ma": float(row["ma_plot"]),
                    "upper": float(row["upper_plot"]),
                    "lower": float(row["lower_plot"]),
                }
                for idx, row in ts_frame.iterrows()
            ]
            payload["timeseries"] = timeseries

            # Compose a concise markdown summary for UI friendliness
            summary = f"""
### TRIN Breadth (Arms Index)
- As of: {payload['as_of']}
- Latest TRIN: {payload['trin']:.3f} (5-day change: {payload['change_5d_pct']:.2f}%)
- 20d MA/Bands: {payload['ma']:.3f} | UBB {payload['upper']:.3f} | LBB {payload['lower']:.3f}
- Band State: {payload['band_state']} | Bias: {payload['bias']}
- Signal: **{payload['signal']}**
- Rationale: {payload['rationale']}

_Primary data source: Nasdaq Data Link (URC datasets) with Yahoo Finance fallback. Contrarian interpretation: elevated TRIN (>1) often signals washout risk; depressed TRIN (<1) can signal euphoria._
            """.strip()

            return json.dumps({"summary": summary, "metrics": payload}, indent=2)
        except Exception as exc:  # pragma: no cover - defensive
            return json.dumps({"error": f"TRIN analysis failed: {exc}"})

    return mcp
