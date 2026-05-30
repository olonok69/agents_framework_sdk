"""Stock Analyzer API - Google ADK multi-agent orchestration endpoints."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .adk_bot import (
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_PROVIDER,
    run_bollinger_fibonacci_analysis,
    run_bollinger_breakout_analysis,
    run_bollinger_zscore_rsi_strategy_analysis,
    run_combined_analysis,
    run_dual_moving_average_analysis,
    run_earnings_momentum_analysis,
    run_fundamental_analysis,
    run_gap_fade_analysis,
    run_macd_donchian_analysis,
    run_market_scanner,
    run_multi_timeframe_analysis,
    run_multi_sector_analysis,
    run_overnight_gap_analysis,
    run_pairs_trading_analysis,
    run_statistical_arbitrage_analysis,
    run_technical_analysis,
    run_trin_breadth_analysis,
    run_vix_term_structure_analysis,
    run_volatility_regime_analysis,
)
from .mcp_tools import (
    bollinger_fibonacci_analysis,
    bollinger_breakout_analysis,
    bollinger_zscore_rsi_strategy_analysis,
    configure_finance_tools,
    dual_moving_average_analysis,
    earnings_momentum_analysis,
    gap_fade_analysis,
    macd_donchian_analysis,
    multi_timeframe_analysis,
    overnight_gap_analysis,
    pairs_trading_analysis,
    statistical_arbitrage_analysis,
    shutdown_finance_tools,
    trin_market_breadth_analysis,
    vix_term_structure_analysis,
    volatility_regime_analysis,
)

load_dotenv()

DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN")
DEFAULT_EARNINGS_SYMBOLS = os.getenv("DEFAULT_EARNINGS_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")
DEFAULT_AGENT_TYPE = "adk_agentic"

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Stock Analyzer API",
    description="Google ADK agentic financial analysis using MCP finance tools.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TechnicalAnalysisRequest(BaseModel):
    """Pydantic request model for TechnicalAnalysis API payloads."""

    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field("1y", description="Analysis period")
    technical_mode: Literal["strategy", "score"] = Field(
        "strategy",
        description="Technical analysis mode: strategy (standalone strategy outputs) or score (comprehensive score model)",
    )
    risk_profile: Literal["conservative", "balanced", "aggressive"] = Field(
        "balanced",
        description="Risk framing profile for recommendations and guardrails",
    )
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider")
    openai_api_key: Optional[str] = Field(None, description="Backward-compat; not used directly")
    hf_token: Optional[str] = Field(None, description="Backward-compat; not used directly")
    max_steps: Optional[int] = Field(None, description="Backward-compat; not used directly")
    agent_type: Optional[str] = Field(None, description="Backward-compat; always uses adk_agentic")
    executor_type: Optional[str] = Field(None, description="Backward-compat; not used directly")


class MarketScannerRequest(BaseModel):
    """Pydantic request model for MarketScanner API payloads."""

    symbols: str = Field(..., description="Comma-separated ticker symbols")
    period: str = Field("1y", description="Analysis period")
    scanner_mode: Literal["strategy", "score"] = Field(
        "strategy",
        description="Scanner analysis mode: strategy (per-strategy consensus framing) or score (aggregate score framing)",
    )
    risk_profile: Literal["conservative", "balanced", "aggressive"] = Field(
        "balanced",
        description="Risk framing profile for recommendations and guardrails",
    )
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    agent_type: Optional[str] = Field(None)
    executor_type: Optional[str] = Field(None)


class FundamentalAnalysisRequest(BaseModel):
    """Pydantic request model for FundamentalAnalysis API payloads."""

    symbol: str = Field(...)
    period: str = Field("3y")
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    agent_type: Optional[str] = Field(None)
    executor_type: Optional[str] = Field(None)


class SectorConfig(BaseModel):
    """Represent SectorConfig behavior and related operations."""

    name: str = Field(...)
    symbols: str = Field(...)


class MultiSectorAnalysisRequest(BaseModel):
    """Pydantic request model for MultiSectorAnalysis API payloads."""

    sectors: List[SectorConfig] = Field(...)
    period: str = Field("1y")
    multisector_mode: Literal["strategy", "score"] = Field(
        "strategy",
        description="Multi-sector analysis mode: strategy (per-strategy consensus framing) or score (aggregate score framing)",
    )
    risk_profile: Literal["conservative", "balanced", "aggressive"] = Field(
        "balanced",
        description="Risk framing profile for recommendations and guardrails",
    )
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    agent_type: Optional[str] = Field(None)
    executor_type: Optional[str] = Field(None)


class CombinedAnalysisRequest(BaseModel):
    """Pydantic request model for CombinedAnalysis API payloads."""

    symbol: str = Field(...)
    technical_period: str = Field("1y")
    fundamental_period: str = Field("3y")
    technical_mode: Literal["strategy", "score"] = Field(
        "strategy",
        description="Mode for the technical branch inside combined analysis",
    )
    risk_profile: Literal["conservative", "balanced", "aggressive"] = Field(
        "balanced",
        description="Risk framing profile for the technical branch recommendations",
    )
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    agent_type: Optional[str] = Field(None)
    executor_type: Optional[str] = Field(None)


class EarningsMomentumRequest(BaseModel):
    """Pydantic request model for EarningsMomentum API payloads."""

    symbols: str = Field(DEFAULT_EARNINGS_SYMBOLS)
    period: str = Field("6mo")
    volume_window: int = Field(20, ge=5, le=60)
    volume_multiplier: float = Field(2.0, ge=1.0, le=5.0)
    hold_days: int = Field(5, ge=1, le=15)
    max_positions: int = Field(3, ge=1, le=10)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    agent_type: Optional[str] = Field(None)
    executor_type: Optional[str] = Field(None)


class TrinAnalysisRequest(BaseModel):
    """Pydantic request model for TrinAnalysis API payloads."""

    period: str = Field("6mo")
    window: int = Field(20, ge=5, le=120)
    band_k: float = Field(1.5, ge=0.5, le=3.0)
    use_log: bool = Field(True)
    agent_type: Optional[str] = Field(None)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class OvernightGapRequest(BaseModel):
    """Pydantic request model for OvernightGap API payloads."""

    symbol: str = Field(...)
    lookback_days: int = Field(120, ge=30, le=400)
    min_gap_pct: float = Field(1.0, ge=0.1, le=20.0)
    agent_type: Optional[str] = Field(None)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class BollingerBreakoutRequest(BaseModel):
    """Pydantic request model for BollingerBreakout API payloads."""

    symbol: str = Field("SPY")
    period: str = Field("2y")
    bb_period: int = Field(20, ge=5, le=100)
    bb_std: float = Field(2.0, ge=0.5, le=5.0)
    atr_period: int = Field(14, ge=5, le=100)
    volume_window: int = Field(20, ge=5, le=100)
    volume_multiplier: float = Field(1.2, ge=0.5, le=5.0)
    warmup_bars: int = Field(25, ge=0, le=200)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class GapFadeRequest(BaseModel):
    """Pydantic request model for GapFade API payloads."""

    symbol: str = Field("SPY")
    period: str = Field("2y")
    gap_threshold: float = Field(0.02, ge=0.005, le=0.1)
    hold_minutes: int = Field(120, ge=15, le=390)
    position_size: float = Field(0.8, ge=0.1, le=1.0)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class MultiTimeframeRequest(BaseModel):
    """Pydantic request model for MultiTimeframe API payloads."""

    symbol: str = Field("SPY")
    period: str = Field("2y")
    sma_fast: int = Field(50, ge=5, le=200)
    sma_slow: int = Field(200, ge=20, le=400)
    rsi_period: int = Field(14, ge=5, le=50)
    rsi_oversold: float = Field(30.0, ge=5.0, le=50.0)
    rsi_exit: float = Field(70.0, ge=50.0, le=95.0)
    warmup_days: int = Field(210, ge=0, le=500)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class PairsTradingRequest(BaseModel):
    """Pydantic request model for PairsTrading API payloads."""

    symbol_a: str = Field("SPY")
    symbol_b: str = Field("QQQ")
    period: str = Field("2y")
    window: int = Field(20, ge=5, le=120)
    entry_threshold: float = Field(2.0, ge=0.5, le=5.0)
    exit_threshold: float = Field(0.5, ge=0.1, le=2.0)
    position_size: float = Field(0.5, ge=0.1, le=1.0)
    warmup_period: int = Field(25, ge=0, le=300)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class StatisticalArbitrageRequest(BaseModel):
    """Pydantic request model for StatisticalArbitrage API payloads."""

    symbols: str = Field("AAPL,MSFT,GOOGL")
    period: str = Field("2y")
    window: int = Field(20, ge=5, le=120)
    entry_threshold: float = Field(1.5, ge=0.5, le=4.0)
    exit_threshold: float = Field(0.3, ge=0.05, le=1.5)
    position_size: float = Field(0.3, ge=0.1, le=1.0)
    warmup_period: int = Field(25, ge=0, le=300)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class VixTermStructureRequest(BaseModel):
    """Pydantic request model for VixTermStructure API payloads."""

    symbol: str = Field("SPY")
    period: str = Field("2y")
    front_window: int = Field(10, ge=5, le=60)
    back_window: int = Field(30, ge=10, le=120)
    contango_threshold: float = Field(1.05, ge=1.0, le=1.5)
    backwardation_threshold: float = Field(0.95, ge=0.5, le=1.0)
    long_position_size: float = Field(0.8, ge=0.1, le=1.0)
    short_position_size: float = Field(-0.5, ge=-1.0, le=-0.1)
    warmup_period: int = Field(35, ge=0, le=300)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class VolatilityRegimeRequest(BaseModel):
    """Pydantic request model for VolatilityRegime API payloads."""

    period: str = Field("2y")
    spy_symbol: str = Field("SPY")
    qqq_symbol: str = Field("QQQ")
    arkk_symbol: str = Field("ARKK")
    tlt_symbol: str = Field("TLT")
    gld_symbol: str = Field("GLD")
    vol_window: int = Field(20, ge=5, le=120)
    high_vol_threshold: float = Field(25.0, ge=10.0, le=80.0)
    low_vol_threshold: float = Field(15.0, ge=5.0, le=40.0)
    warmup_period: int = Field(25, ge=0, le=300)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class BollingerZscoreRsiStrategyRequest(BaseModel):
    """Pydantic request model for BollingerZscoreRsiStrategy API payloads."""

    symbol: str = Field("AAPL")
    period: str = Field("2y")
    bb_window: int = Field(20, ge=5, le=200)
    bb_std: float = Field(2.0, ge=0.5, le=5.0)
    rsi_period: int = Field(14, ge=2, le=100)
    rsi_oversold: float = Field(30.0, ge=1.0, le=50.0)
    rsi_overbought: float = Field(70.0, ge=50.0, le=99.0)
    zscore_buy_threshold: float = Field(-2.0, ge=-5.0, le=-0.5)
    zscore_sell_threshold: float = Field(2.0, ge=0.5, le=5.0)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class BollingerFibonacciRequest(BaseModel):
    """Pydantic request model for BollingerFibonacci API payloads."""

    symbol: str = Field("AAPL")
    period: str = Field("1y")
    window: int = Field(20, ge=5, le=200)
    num_std: int = Field(2, ge=1, le=5)
    window_swing_points: int = Field(10, ge=3, le=50)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class MacdDonchianRequest(BaseModel):
    """Pydantic request model for MacdDonchian API payloads."""

    symbol: str = Field("AAPL")
    period: str = Field("1y")
    fast_period: int = Field(12, ge=2, le=100)
    slow_period: int = Field(26, ge=5, le=200)
    signal_period: int = Field(9, ge=2, le=60)
    window: int = Field(20, ge=5, le=200)
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class DualMovingAverageRequest(BaseModel):
    """Pydantic request model for DualMovingAverage API payloads."""

    symbol: str = Field("AAPL")
    period: str = Field("2y")
    short_period: int = Field(50, ge=2, le=200)
    long_period: int = Field(200, ge=5, le=500)
    ma_type: str = Field("SMA")
    model_id: Optional[str] = Field(None)
    model_provider: Optional[str] = Field(None)
    openai_api_key: Optional[str] = Field(None)
    hf_token: Optional[str] = Field(None)


class AnalysisResponse(BaseModel):
    """Pydantic response model for Analysis API responses."""

    report: str = Field(...)
    symbol: str = Field(...)
    analysis_type: str = Field(...)
    duration_seconds: float = Field(...)
    agent_type: str = Field(...)
    tools_approach: str = Field(...)
    timeseries: Optional[List[dict]] = Field(None)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    """Handle API healthcheck lifecycle behavior."""

    return {
        "status": "ok",
        "version": "4.0.0",
        "features": [
            "technical_analysis",
            "market_scanner",
            "fundamental_analysis",
            "multi_sector_analysis",
            "combined_analysis",
            "earnings_momentum",
            "trin_breadth",
            "overnight_gaps",
            "bollinger_breakout",
            "gap_fade",
            "multi_timeframe",
            "pairs_trading",
            "statistical_arbitrage",
            "vix_term_structure",
            "volatility_regime",
            "bollinger_zscore_rsi",
            "bollinger_fibonacci",
            "macd_donchian",
            "dual_moving_average",
        ],
        "agent_types": {
            "adk_agentic": {
                "available": True,
                "approach": "orchestrator + financial specialist + critic + reporting specialist",
            }
        },
        "default_agent_type": DEFAULT_AGENT_TYPE,
        "model": {
            "default_id": DEFAULT_MODEL_ID,
            "default_provider": DEFAULT_MODEL_PROVIDER,
        },
    }


def _adk_model(request_model_id: Optional[str]) -> str:
    """Resolve model."""

    return request_model_id or DEFAULT_MODEL_ID


@app.post("/technical", tags=["analysis"], response_model=AnalysisResponse)
async def technical_analysis(request: TechnicalAnalysisRequest) -> dict:
    """Implement technical analysis."""

    start_time = time.time()
    try:
        result = await run_in_threadpool(
            run_technical_analysis,
            symbol=request.symbol,
            period=request.period,
            technical_mode=request.technical_mode,
            risk_profile=request.risk_profile,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    mode_approach = (
        "MCP standalone strategy bundle + ADK multi-agent review"
        if request.technical_mode == "strategy"
        else "MCP high-level score model + ADK multi-agent review"
    )

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "technical",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": mode_approach,
    }


@app.post("/scanner", tags=["analysis"], response_model=AnalysisResponse)
async def market_scanner(request: MarketScannerRequest) -> dict:
    """Implement market scanner."""

    start_time = time.time()
    try:
        result = await run_in_threadpool(
            run_market_scanner,
            symbols=request.symbols,
            period=request.period,
            scanner_mode=request.scanner_mode,
            risk_profile=request.risk_profile,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scanner failed: {exc}") from exc

    mode_approach = (
        "MCP scanner strategy-consensus view + ADK multi-agent review"
        if request.scanner_mode == "strategy"
        else "MCP scanner score-synthesis view + ADK multi-agent review"
    )

    return {
        "report": result,
        "symbol": request.symbols.upper(),
        "analysis_type": "scanner",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": mode_approach,
    }


@app.post("/fundamental", tags=["analysis"], response_model=AnalysisResponse)
async def fundamental_analysis(request: FundamentalAnalysisRequest) -> dict:
    """Implement fundamental analysis."""

    start_time = time.time()
    try:
        result = await run_in_threadpool(
            run_fundamental_analysis,
            symbol=request.symbol,
            period=request.period,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "fundamental",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP fundamental tool + ADK multi-agent review",
    }


@app.post("/multisector", tags=["analysis"], response_model=AnalysisResponse)
async def multi_sector_analysis(request: MultiSectorAnalysisRequest) -> dict:
    """Implement multi sector analysis."""

    start_time = time.time()
    sectors_dict = {sector.name: sector.symbols for sector in request.sectors}
    try:
        result = await run_in_threadpool(
            run_multi_sector_analysis,
            sectors=sectors_dict,
            period=request.period,
            multisector_mode=request.multisector_mode,
            risk_profile=request.risk_profile,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    mode_approach = (
        "MCP scanner per-sector strategy-consensus view + ADK multi-agent review"
        if request.multisector_mode == "strategy"
        else "MCP scanner per-sector score-synthesis view + ADK multi-agent review"
    )

    return {
        "report": result,
        "symbol": ", ".join(sectors_dict.keys()),
        "analysis_type": "multi_sector",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": mode_approach,
    }


@app.post("/combined", tags=["analysis"], response_model=AnalysisResponse)
async def combined_analysis(request: CombinedAnalysisRequest) -> dict:
    """Implement combined analysis."""

    start_time = time.time()
    try:
        result = await run_in_threadpool(
            run_combined_analysis,
            symbol=request.symbol,
            technical_period=request.technical_period,
            fundamental_period=request.fundamental_period,
            technical_mode=request.technical_mode,
            risk_profile=request.risk_profile,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    mode_approach = (
        "MCP technical strategy-consensus + fundamental tools + ADK multi-agent synthesis"
        if request.technical_mode == "strategy"
        else "MCP technical score-synthesis + fundamental tools + ADK multi-agent synthesis"
    )

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "combined",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": mode_approach,
    }


@app.post("/earnings_momentum", tags=["analysis"], response_model=AnalysisResponse)
async def earnings_momentum(request: EarningsMomentumRequest) -> dict:
    """Implement earnings momentum."""

    start_time = time.time()

    try:
        result = await run_in_threadpool(
            run_earnings_momentum_analysis,
            symbols=request.symbols,
            period=request.period,
            volume_window=request.volume_window,
            volume_multiplier=request.volume_multiplier,
            hold_days=request.hold_days,
            max_positions=request.max_positions,
            model_id=_adk_model(request.model_id),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Earnings momentum analysis failed: {exc}") from exc

    timeseries = None
    try:
        raw_metrics = await run_in_threadpool(
            earnings_momentum_analysis,
            symbols=request.symbols,
            period=request.period,
            volume_window=request.volume_window,
            volume_multiplier=request.volume_multiplier,
            hold_days=request.hold_days,
            max_positions=request.max_positions,
        )
        parsed = json.loads(raw_metrics)
        metrics_block = parsed.get("metrics") if isinstance(parsed, dict) else None
        if isinstance(metrics_block, dict):
            timeseries = metrics_block.get("signals") or metrics_block.get("trades")
    except Exception:
        timeseries = None

    return {
        "report": result,
        "symbol": request.symbols,
        "analysis_type": "earnings_momentum",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP earnings tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/trin", tags=["analysis"], response_model=AnalysisResponse)
async def trin_breadth_analysis(request: TrinAnalysisRequest) -> dict:
    """Implement trin breadth analysis."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_trin_breadth_analysis,
            period=request.period,
            window=request.window,
            band_k=request.band_k,
            use_log=request.use_log,
            model_id=_adk_model(request.model_id),
        )
        raw = await run_in_threadpool(
            trin_market_breadth_analysis,
            period=request.period,
            window=request.window,
            band_k=request.band_k,
            use_log=request.use_log,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("timeseries")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TRIN analysis failed: {exc}") from exc

    return {
        "report": result,
        "symbol": "TRIN (Arms Index)",
        "analysis_type": "trin",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP TRIN tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/overnight_gaps", tags=["analysis"], response_model=AnalysisResponse)
async def overnight_gaps(request: OvernightGapRequest) -> dict:
    """Implement overnight gaps."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_overnight_gap_analysis,
            symbol=request.symbol,
            lookback_days=request.lookback_days,
            min_gap_pct=request.min_gap_pct,
            model_id=_adk_model(request.model_id),
        )
        raw = await run_in_threadpool(
            overnight_gap_analysis,
            symbol=request.symbol,
            lookback_days=request.lookback_days,
            min_gap_pct=request.min_gap_pct,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("timeseries")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Overnight gaps failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "overnight_gaps",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP overnight gap tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/bollinger_breakout", tags=["strategy"], response_model=AnalysisResponse)
async def bollinger_breakout(request: BollingerBreakoutRequest) -> dict:
    """Implement bollinger breakout."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_bollinger_breakout_analysis,
            symbol=request.symbol,
            period=request.period,
            bb_period=request.bb_period,
            bb_std=request.bb_std,
            atr_period=request.atr_period,
            volume_window=request.volume_window,
            volume_multiplier=request.volume_multiplier,
            warmup_bars=request.warmup_bars,
            model_id=_adk_model(request.model_id),
        )
        raw = await run_in_threadpool(
            bollinger_breakout_analysis,
            symbol=request.symbol,
            period=request.period,
            bb_period=request.bb_period,
            bb_std=request.bb_std,
            atr_period=request.atr_period,
            volume_window=request.volume_window,
            volume_multiplier=request.volume_multiplier,
            warmup_bars=request.warmup_bars,
        )
        try:
            parsed = json.loads(raw)
            metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
            if isinstance(metrics, dict):
                timeseries = metrics.get("trades")
        except Exception:
            timeseries = None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Bollinger breakout failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "bollinger_breakout",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP Bollinger breakout tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/gap_fade", tags=["strategy"], response_model=AnalysisResponse)
async def gap_fade(request: GapFadeRequest) -> dict:
    """Implement gap fade."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_gap_fade_analysis,
            symbol=request.symbol,
            period=request.period,
            gap_threshold=request.gap_threshold,
            hold_minutes=request.hold_minutes,
            position_size=request.position_size,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            gap_fade_analysis,
            symbol=request.symbol,
            period=request.period,
            gap_threshold=request.gap_threshold,
            hold_minutes=request.hold_minutes,
            position_size=request.position_size,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gap fade failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "gap_fade",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP gap fade tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/multi_timeframe", tags=["strategy"], response_model=AnalysisResponse)
async def multi_timeframe(request: MultiTimeframeRequest) -> dict:
    """Implement multi timeframe."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_multi_timeframe_analysis,
            symbol=request.symbol,
            period=request.period,
            sma_fast=request.sma_fast,
            sma_slow=request.sma_slow,
            rsi_period=request.rsi_period,
            rsi_oversold=request.rsi_oversold,
            rsi_exit=request.rsi_exit,
            warmup_days=request.warmup_days,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            multi_timeframe_analysis,
            symbol=request.symbol,
            period=request.period,
            sma_fast=request.sma_fast,
            sma_slow=request.sma_slow,
            rsi_period=request.rsi_period,
            rsi_oversold=request.rsi_oversold,
            rsi_exit=request.rsi_exit,
            warmup_days=request.warmup_days,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multi-timeframe failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "multi_timeframe",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP multi-timeframe tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/pairs_trading", tags=["strategy"], response_model=AnalysisResponse)
async def pairs_trading(request: PairsTradingRequest) -> dict:
    """Implement pairs trading."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    pair_label = f"{request.symbol_a.upper()}/{request.symbol_b.upper()}"
    try:
        result = await run_in_threadpool(
            run_pairs_trading_analysis,
            symbol_a=request.symbol_a,
            symbol_b=request.symbol_b,
            period=request.period,
            window=request.window,
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            position_size=request.position_size,
            warmup_period=request.warmup_period,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            pairs_trading_analysis,
            symbol_a=request.symbol_a,
            symbol_b=request.symbol_b,
            period=request.period,
            window=request.window,
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            position_size=request.position_size,
            warmup_period=request.warmup_period,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pairs trading failed: {exc}") from exc

    return {
        "report": result,
        "symbol": pair_label,
        "analysis_type": "pairs_trading",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP pairs trading tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/statistical_arbitrage", tags=["strategy"], response_model=AnalysisResponse)
async def statistical_arbitrage(request: StatisticalArbitrageRequest) -> dict:
    """Implement statistical arbitrage."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_statistical_arbitrage_analysis,
            symbols=request.symbols,
            period=request.period,
            window=request.window,
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            position_size=request.position_size,
            warmup_period=request.warmup_period,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            statistical_arbitrage_analysis,
            symbols=request.symbols,
            period=request.period,
            window=request.window,
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            position_size=request.position_size,
            warmup_period=request.warmup_period,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Statistical arbitrage failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbols.upper(),
        "analysis_type": "statistical_arbitrage",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP statistical arbitrage tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/vix_term_structure", tags=["strategy"], response_model=AnalysisResponse)
async def vix_term_structure(request: VixTermStructureRequest) -> dict:
    """Implement vix term structure."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_vix_term_structure_analysis,
            symbol=request.symbol,
            period=request.period,
            front_window=request.front_window,
            back_window=request.back_window,
            contango_threshold=request.contango_threshold,
            backwardation_threshold=request.backwardation_threshold,
            long_position_size=request.long_position_size,
            short_position_size=request.short_position_size,
            warmup_period=request.warmup_period,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            vix_term_structure_analysis,
            symbol=request.symbol,
            period=request.period,
            front_window=request.front_window,
            back_window=request.back_window,
            contango_threshold=request.contango_threshold,
            backwardation_threshold=request.backwardation_threshold,
            long_position_size=request.long_position_size,
            short_position_size=request.short_position_size,
            warmup_period=request.warmup_period,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"VIX term structure failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "vix_term_structure",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP VIX term structure tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/volatility_regime", tags=["strategy"], response_model=AnalysisResponse)
async def volatility_regime(request: VolatilityRegimeRequest) -> dict:
    """Implement volatility regime."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_volatility_regime_analysis,
            period=request.period,
            spy_symbol=request.spy_symbol,
            qqq_symbol=request.qqq_symbol,
            arkk_symbol=request.arkk_symbol,
            tlt_symbol=request.tlt_symbol,
            gld_symbol=request.gld_symbol,
            vol_window=request.vol_window,
            high_vol_threshold=request.high_vol_threshold,
            low_vol_threshold=request.low_vol_threshold,
            warmup_period=request.warmup_period,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            volatility_regime_analysis,
            period=request.period,
            spy_symbol=request.spy_symbol,
            qqq_symbol=request.qqq_symbol,
            arkk_symbol=request.arkk_symbol,
            tlt_symbol=request.tlt_symbol,
            gld_symbol=request.gld_symbol,
            vol_window=request.vol_window,
            high_vol_threshold=request.high_vol_threshold,
            low_vol_threshold=request.low_vol_threshold,
            warmup_period=request.warmup_period,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("regime_events")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Volatility regime failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.spy_symbol.upper(),
        "analysis_type": "volatility_regime",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP volatility regime tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/bollinger_zscore_rsi", tags=["strategy"], response_model=AnalysisResponse)
async def bollinger_zscore_rsi(request: BollingerZscoreRsiStrategyRequest) -> dict:
    """Implement bollinger zscore rsi."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_bollinger_zscore_rsi_strategy_analysis,
            symbol=request.symbol,
            period=request.period,
            bb_window=request.bb_window,
            bb_std=request.bb_std,
            rsi_period=request.rsi_period,
            rsi_oversold=request.rsi_oversold,
            rsi_overbought=request.rsi_overbought,
            zscore_buy_threshold=request.zscore_buy_threshold,
            zscore_sell_threshold=request.zscore_sell_threshold,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            bollinger_zscore_rsi_strategy_analysis,
            symbol=request.symbol,
            period=request.period,
            bb_window=request.bb_window,
            bb_std=request.bb_std,
            rsi_period=request.rsi_period,
            rsi_oversold=request.rsi_oversold,
            rsi_overbought=request.rsi_overbought,
            zscore_buy_threshold=request.zscore_buy_threshold,
            zscore_sell_threshold=request.zscore_sell_threshold,
        )
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
        if isinstance(metrics, dict):
            timeseries = metrics.get("trades")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Bollinger Z-Score RSI strategy failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "bollinger_zscore_rsi",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP Bollinger Z-Score RSI strategy tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/bollinger_fibonacci", tags=["strategy"], response_model=AnalysisResponse)
async def bollinger_fibonacci(request: BollingerFibonacciRequest) -> dict:
    """Implement bollinger fibonacci."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_bollinger_fibonacci_analysis,
            symbol=request.symbol,
            period=request.period,
            window=request.window,
            num_std=request.num_std,
            window_swing_points=request.window_swing_points,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            bollinger_fibonacci_analysis,
            symbol=request.symbol,
            period=request.period,
            window=request.window,
            num_std=request.num_std,
            window_swing_points=request.window_swing_points,
        )
        try:
            parsed = json.loads(raw)
            metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
            if isinstance(metrics, dict):
                timeseries = metrics.get("trades")
        except Exception:
            timeseries = None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Bollinger Fibonacci failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "bollinger_fibonacci",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP Bollinger Fibonacci strategy tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/macd_donchian", tags=["strategy"], response_model=AnalysisResponse)
async def macd_donchian(request: MacdDonchianRequest) -> dict:
    """Implement macd donchian."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_macd_donchian_analysis,
            symbol=request.symbol,
            period=request.period,
            fast_period=request.fast_period,
            slow_period=request.slow_period,
            signal_period=request.signal_period,
            window=request.window,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            macd_donchian_analysis,
            symbol=request.symbol,
            period=request.period,
            fast_period=request.fast_period,
            slow_period=request.slow_period,
            signal_period=request.signal_period,
            window=request.window,
        )
        try:
            parsed = json.loads(raw)
            metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
            if isinstance(metrics, dict):
                timeseries = metrics.get("trades")
        except Exception:
            timeseries = None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MACD Donchian failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "macd_donchian",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP MACD Donchian strategy tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.post("/dual_moving_average", tags=["strategy"], response_model=AnalysisResponse)
async def dual_moving_average(request: DualMovingAverageRequest) -> dict:
    """Implement dual moving average."""

    start_time = time.time()
    timeseries: Optional[List[dict]] = None
    try:
        result = await run_in_threadpool(
            run_dual_moving_average_analysis,
            symbol=request.symbol,
            period=request.period,
            short_period=request.short_period,
            long_period=request.long_period,
            ma_type=request.ma_type,
            model_id=_adk_model(request.model_id),
        )

        raw = await run_in_threadpool(
            dual_moving_average_analysis,
            symbol=request.symbol,
            period=request.period,
            short_period=request.short_period,
            long_period=request.long_period,
            ma_type=request.ma_type,
        )
        try:
            parsed = json.loads(raw)
            metrics = parsed.get("metrics", {}) if isinstance(parsed, dict) else {}
            if isinstance(metrics, dict):
                timeseries = metrics.get("trades")
        except Exception:
            timeseries = None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dual moving average failed: {exc}") from exc

    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "dual_moving_average",
        "duration_seconds": round(time.time() - start_time, 2),
        "agent_type": DEFAULT_AGENT_TYPE,
        "tools_approach": "MCP Dual MA strategy tool + ADK multi-agent review",
        "timeseries": timeseries,
    }


@app.on_event("startup")
async def startup_event():
    """Handle API startup event lifecycle behavior."""

    logger.info("Starting Stock Analyzer API v4.0.0 (ADK)")
    logger.info("Default model: %s", DEFAULT_MODEL_ID)
    try:
        configure_finance_tools()
        logger.info("MCP tools configured successfully")
    except Exception as exc:
        logger.error("Failed to configure MCP tools: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    """Handle API shutdown event lifecycle behavior."""

    logger.info("Shutting down Stock Analyzer API")
    try:
        shutdown_finance_tools()
        logger.info("MCP tools shutdown successfully")
    except Exception as exc:
        logger.error("Error during MCP shutdown: %s", exc)
