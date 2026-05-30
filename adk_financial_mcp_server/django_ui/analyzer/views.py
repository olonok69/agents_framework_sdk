from __future__ import annotations

import time
from typing import Dict, List

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404, HttpResponse
from django.shortcuts import render

from .forms import RegisterForm
from .models import SavedReport
from .services import call_backend

DEFAULT_SETTINGS = {
    "api_url": "http://localhost:8000",
    "model_id": "gpt-4.1",
    "model_provider": "openai",
    "openai_api_key": "",
}

DEFAULT_THEME = {
    "bg_color": "#f5f7fb",
    "surface_color": "#ffffff",
    "text_color": "#1c2636",
    "accent_color": "#265cff",
    "primary_button_text_color": "#ffffff",
    "secondary_button_text_color": "#ffffff",
}


def _session_settings(request) -> Dict[str, str]:
    settings = request.session.get("ui_settings", {})
    merged = {**DEFAULT_SETTINGS, **settings}
    request.session["ui_settings"] = merged
    return merged


def _session_theme(request) -> Dict[str, str]:
    theme = request.session.get("ui_theme", {})
    merged = {**DEFAULT_THEME, **theme}
    request.session["ui_theme"] = merged
    return merged


def _to_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def _to_float(value: str, fallback: float) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _sectors_payload(names: str, symbols: str) -> List[dict]:
    name_lines = [line.strip() for line in names.splitlines() if line.strip()]
    symbol_lines = [line.strip() for line in symbols.splitlines() if line.strip()]
    sectors: List[dict] = []
    for idx, name in enumerate(name_lines):
        if idx < len(symbol_lines):
            sectors.append({"name": name, "symbols": symbol_lines[idx]})
    if not sectors:
        sectors = [
            {"name": "Banking", "symbols": "JPM,BAC,WFC"},
            {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"},
        ]
    return sectors


def _payload_from_action(action: str, post_data) -> tuple[str, dict, str]:
    if action == "technical":
        selected_mode = post_data.get("tech_mode", "strategy").strip().lower()
        if selected_mode not in {"strategy", "score"}:
            selected_mode = "strategy"
        selected_risk_profile = post_data.get("tech_risk_profile", "balanced").strip().lower()
        if selected_risk_profile not in {"conservative", "balanced", "aggressive"}:
            selected_risk_profile = "balanced"
        return (
            "technical",
            {
                "symbol": post_data.get("tech_symbol", "AAPL"),
                "period": post_data.get("tech_period", "1y"),
                "technical_mode": selected_mode,
                "risk_profile": selected_risk_profile,
            },
            f"Technical ({selected_mode}, {selected_risk_profile}): {post_data.get('tech_symbol', 'AAPL').upper()}",
        )

    if action == "scanner":
        symbols = post_data.get("scanner_symbols", "AAPL,MSFT,GOOGL,AMZN")
        selected_mode = post_data.get("scanner_mode", "strategy").strip().lower()
        if selected_mode not in {"strategy", "score"}:
            selected_mode = "strategy"
        selected_risk_profile = post_data.get("scanner_risk_profile", "balanced").strip().lower()
        if selected_risk_profile not in {"conservative", "balanced", "aggressive"}:
            selected_risk_profile = "balanced"
        return (
            "scanner",
            {
                "symbols": symbols,
                "period": post_data.get("scanner_period", "1y"),
                "scanner_mode": selected_mode,
                "risk_profile": selected_risk_profile,
            },
            f"Scanner ({selected_mode}, {selected_risk_profile}): {symbols}",
        )

    if action == "fundamental":
        symbol = post_data.get("fund_symbol", "MSFT")
        return (
            "fundamental",
            {
                "symbol": symbol,
                "period": post_data.get("fund_period", "3y"),
            },
            f"Fundamental: {symbol.upper()}",
        )

    if action == "multisector":
        names = post_data.get("sector_names", "Banking\nTechnology")
        symbols = post_data.get("sector_symbols", "JPM,BAC,WFC\nAAPL,MSFT,GOOGL")
        sectors = _sectors_payload(names, symbols)
        selected_mode = post_data.get("multi_mode", "strategy").strip().lower()
        if selected_mode not in {"strategy", "score"}:
            selected_mode = "strategy"
        selected_risk_profile = post_data.get("multi_risk_profile", "balanced").strip().lower()
        if selected_risk_profile not in {"conservative", "balanced", "aggressive"}:
            selected_risk_profile = "balanced"
        return (
            "multisector",
            {
                "period": post_data.get("multi_period", "1y"),
                "sectors": sectors,
                "multisector_mode": selected_mode,
                "risk_profile": selected_risk_profile,
            },
            f"Multi-Sector ({selected_mode}, {selected_risk_profile})",
        )

    if action == "combined":
        symbol = post_data.get("combined_symbol", "TSLA")
        selected_mode = post_data.get("combined_tech_mode", "strategy").strip().lower()
        if selected_mode not in {"strategy", "score"}:
            selected_mode = "strategy"
        selected_risk_profile = post_data.get("combined_risk_profile", "balanced").strip().lower()
        if selected_risk_profile not in {"conservative", "balanced", "aggressive"}:
            selected_risk_profile = "balanced"
        return (
            "combined",
            {
                "symbol": symbol,
                "technical_period": post_data.get("combined_tech_period", "1y"),
                "fundamental_period": post_data.get("combined_fund_period", "3y"),
                "technical_mode": selected_mode,
                "risk_profile": selected_risk_profile,
            },
            f"Combined ({selected_mode}, {selected_risk_profile}): {symbol.upper()}",
        )

    if action == "overnight_gaps":
        symbol = post_data.get("gap_symbol", "AAPL")
        return (
            "overnight_gaps",
            {
                "symbol": symbol,
                "lookback_days": _to_int(post_data.get("lookback_days", "120"), 120),
                "min_gap_pct": _to_float(post_data.get("min_gap_pct", "1.0"), 1.0),
            },
            f"Overnight Gaps: {symbol.upper()}",
        )

    if action == "earnings_momentum":
        symbols = post_data.get("earnings_symbols", "AAPL,MSFT,GOOGL,AMZN,NVDA")
        return (
            "earnings_momentum",
            {
                "symbols": symbols,
                "period": post_data.get("earnings_period", "6mo"),
                "volume_window": _to_int(post_data.get("volume_window", "20"), 20),
                "volume_multiplier": _to_float(post_data.get("volume_multiplier", "2.0"), 2.0),
                "hold_days": _to_int(post_data.get("hold_days", "5"), 5),
                "max_positions": _to_int(post_data.get("max_positions", "3"), 3),
            },
            f"Earnings Momentum: {symbols}",
        )

    if action == "bollinger_breakout":
        symbol = post_data.get("bb_symbol", "SPY")
        return (
            "bollinger_breakout",
            {
                "symbol": symbol,
                "period": post_data.get("bb_period_window", "2y"),
                "bb_period": _to_int(post_data.get("bb_period", "20"), 20),
                "bb_std": _to_float(post_data.get("bb_std", "2.0"), 2.0),
                "atr_period": _to_int(post_data.get("bb_atr_period", "14"), 14),
                "volume_window": _to_int(post_data.get("bb_volume_window", "20"), 20),
                "volume_multiplier": _to_float(post_data.get("bb_volume_multiplier", "1.2"), 1.2),
                "warmup_bars": _to_int(post_data.get("bb_warmup_bars", "25"), 25),
            },
            f"Bollinger Breakout: {symbol.upper()}",
        )

    if action == "gap_fade":
        symbol = post_data.get("gf_symbol", "SPY")
        return (
            "gap_fade",
            {
                "symbol": symbol,
                "period": post_data.get("gf_period", "2y"),
                "gap_threshold": _to_float(post_data.get("gf_gap_threshold", "0.02"), 0.02),
                "hold_minutes": _to_int(post_data.get("gf_hold_minutes", "120"), 120),
                "position_size": _to_float(post_data.get("gf_position_size", "0.8"), 0.8),
            },
            f"Gap Fade: {symbol.upper()}",
        )

    if action == "multi_timeframe":
        symbol = post_data.get("mt_symbol", "SPY")
        return (
            "multi_timeframe",
            {
                "symbol": symbol,
                "period": post_data.get("mt_period", "2y"),
                "sma_fast": _to_int(post_data.get("mt_sma_fast", "50"), 50),
                "sma_slow": _to_int(post_data.get("mt_sma_slow", "200"), 200),
                "rsi_period": _to_int(post_data.get("mt_rsi_period", "14"), 14),
                "rsi_oversold": _to_float(post_data.get("mt_rsi_oversold", "30"), 30.0),
                "rsi_exit": _to_float(post_data.get("mt_rsi_exit", "70"), 70.0),
                "warmup_days": _to_int(post_data.get("mt_warmup_days", "210"), 210),
            },
            f"Multi-Timeframe: {symbol.upper()}",
        )

    if action == "pairs_trading":
        symbol_a = post_data.get("pt_symbol_a", "SPY")
        symbol_b = post_data.get("pt_symbol_b", "QQQ")
        return (
            "pairs_trading",
            {
                "symbol_a": symbol_a,
                "symbol_b": symbol_b,
                "period": post_data.get("pt_period", "2y"),
                "window": _to_int(post_data.get("pt_window", "20"), 20),
                "entry_threshold": _to_float(post_data.get("pt_entry_threshold", "2.0"), 2.0),
                "exit_threshold": _to_float(post_data.get("pt_exit_threshold", "0.5"), 0.5),
                "position_size": _to_float(post_data.get("pt_position_size", "0.5"), 0.5),
                "warmup_period": _to_int(post_data.get("pt_warmup_period", "25"), 25),
            },
            f"Pairs Trading: {symbol_a.upper()}/{symbol_b.upper()}",
        )

    if action == "statistical_arbitrage":
        symbols = post_data.get("sa_symbols", "AAPL,MSFT,GOOGL")
        return (
            "statistical_arbitrage",
            {
                "symbols": symbols,
                "period": post_data.get("sa_period", "2y"),
                "window": _to_int(post_data.get("sa_window", "20"), 20),
                "entry_threshold": _to_float(post_data.get("sa_entry_threshold", "1.5"), 1.5),
                "exit_threshold": _to_float(post_data.get("sa_exit_threshold", "0.3"), 0.3),
                "position_size": _to_float(post_data.get("sa_position_size", "0.3"), 0.3),
                "warmup_period": _to_int(post_data.get("sa_warmup_period", "25"), 25),
            },
            f"Statistical Arbitrage: {symbols}",
        )

    if action == "vix_term_structure":
        symbol = post_data.get("vts_symbol", "SPY")
        return (
            "vix_term_structure",
            {
                "symbol": symbol,
                "period": post_data.get("vts_period", "2y"),
                "front_window": _to_int(post_data.get("vts_front_window", "10"), 10),
                "back_window": _to_int(post_data.get("vts_back_window", "30"), 30),
                "contango_threshold": _to_float(post_data.get("vts_contango_threshold", "1.05"), 1.05),
                "backwardation_threshold": _to_float(post_data.get("vts_backwardation_threshold", "0.95"), 0.95),
                "long_position_size": _to_float(post_data.get("vts_long_position_size", "0.8"), 0.8),
                "short_position_size": _to_float(post_data.get("vts_short_position_size", "-0.5"), -0.5),
                "warmup_period": _to_int(post_data.get("vts_warmup_period", "35"), 35),
            },
            f"VIX Term Structure: {symbol.upper()}",
        )

    if action == "volatility_regime":
        return (
            "volatility_regime",
            {
                "period": post_data.get("vr_period", "2y"),
                "spy_symbol": post_data.get("vr_spy_symbol", "SPY"),
                "qqq_symbol": post_data.get("vr_qqq_symbol", "QQQ"),
                "arkk_symbol": post_data.get("vr_arkk_symbol", "ARKK"),
                "tlt_symbol": post_data.get("vr_tlt_symbol", "TLT"),
                "gld_symbol": post_data.get("vr_gld_symbol", "GLD"),
                "vol_window": _to_int(post_data.get("vr_vol_window", "20"), 20),
                "high_vol_threshold": _to_float(post_data.get("vr_high_vol_threshold", "25.0"), 25.0),
                "low_vol_threshold": _to_float(post_data.get("vr_low_vol_threshold", "15.0"), 15.0),
                "warmup_period": _to_int(post_data.get("vr_warmup_period", "25"), 25),
            },
            "Volatility Regime",
        )

    if action == "bollinger_zscore_rsi":
        symbol = post_data.get("bzrsi_symbol", "AAPL")
        return (
            "bollinger_zscore_rsi",
            {
                "symbol": symbol,
                "period": post_data.get("bzrsi_period", "2y"),
                "bb_window": _to_int(post_data.get("bzrsi_bb_window", "20"), 20),
                "bb_std": _to_float(post_data.get("bzrsi_bb_std", "2.0"), 2.0),
                "rsi_period": _to_int(post_data.get("bzrsi_rsi_period", "14"), 14),
                "rsi_oversold": _to_float(post_data.get("bzrsi_rsi_oversold", "30.0"), 30.0),
                "rsi_overbought": _to_float(post_data.get("bzrsi_rsi_overbought", "70.0"), 70.0),
                "zscore_buy_threshold": _to_float(post_data.get("bzrsi_z_buy", "-2.0"), -2.0),
                "zscore_sell_threshold": _to_float(post_data.get("bzrsi_z_sell", "2.0"), 2.0),
            },
            f"Bollinger Z-Score RSI: {symbol.upper()}",
        )

    if action == "bollinger_fibonacci":
        symbol = post_data.get("bf_symbol", "AAPL")
        return (
            "bollinger_fibonacci",
            {
                "symbol": symbol,
                "period": post_data.get("bf_period", "1y"),
                "window": _to_int(post_data.get("bf_window", "20"), 20),
                "num_std": _to_int(post_data.get("bf_num_std", "2"), 2),
                "window_swing_points": _to_int(post_data.get("bf_window_swing_points", "10"), 10),
            },
            f"Bollinger Fibonacci: {symbol.upper()}",
        )

    if action == "macd_donchian":
        symbol = post_data.get("md_symbol", "AAPL")
        return (
            "macd_donchian",
            {
                "symbol": symbol,
                "period": post_data.get("md_period", "1y"),
                "fast_period": _to_int(post_data.get("md_fast_period", "12"), 12),
                "slow_period": _to_int(post_data.get("md_slow_period", "26"), 26),
                "signal_period": _to_int(post_data.get("md_signal_period", "9"), 9),
                "window": _to_int(post_data.get("md_window", "20"), 20),
            },
            f"MACD Donchian: {symbol.upper()}",
        )

    if action == "dual_moving_average":
        symbol = post_data.get("dma_symbol", "AAPL")
        return (
            "dual_moving_average",
            {
                "symbol": symbol,
                "period": post_data.get("dma_period", "2y"),
                "short_period": _to_int(post_data.get("dma_short_period", "50"), 50),
                "long_period": _to_int(post_data.get("dma_long_period", "200"), 200),
                "ma_type": post_data.get("dma_ma_type", "SMA"),
            },
            f"Dual Moving Average: {symbol.upper()}",
        )

    raise ValueError("Unsupported action")


def _apply_model_settings(payload: dict, settings: Dict[str, str]) -> dict:
    if settings.get("model_id"):
        payload["model_id"] = settings["model_id"]
    if settings.get("model_provider"):
        payload["model_provider"] = settings["model_provider"]
    if settings.get("openai_api_key"):
        payload["openai_api_key"] = settings["openai_api_key"]
    return payload


def index(request):
    settings = _session_settings(request)
    theme = _session_theme(request)
    history = request.session.get("analysis_history", [])
    result = None
    error = None
    active_tab = "technical"
    selected_saved = None
    selected_history = None

    selected_id = request.GET.get("saved")
    if request.user.is_authenticated and selected_id:
        try:
            selected_saved = SavedReport.objects.get(id=int(selected_id), user=request.user)
        except Exception:
            selected_saved = None

    if request.method == "POST":
        action = request.POST.get("action", "technical")

        if action == "save_settings":
            request.session["ui_settings"] = {
                "api_url": request.POST.get("api_url", DEFAULT_SETTINGS["api_url"]),
                "model_id": request.POST.get("model_id", DEFAULT_SETTINGS["model_id"]),
                "model_provider": request.POST.get("model_provider", DEFAULT_SETTINGS["model_provider"]),
                "openai_api_key": request.POST.get("openai_api_key", ""),
            }
            settings = _session_settings(request)
        elif action == "save_theme":
            request.session["ui_theme"] = {
                "bg_color": request.POST.get("bg_color", DEFAULT_THEME["bg_color"]),
                "surface_color": request.POST.get("surface_color", DEFAULT_THEME["surface_color"]),
                "text_color": request.POST.get("text_color", DEFAULT_THEME["text_color"]),
                "accent_color": request.POST.get("accent_color", DEFAULT_THEME["accent_color"]),
                "primary_button_text_color": request.POST.get(
                    "primary_button_text_color", DEFAULT_THEME["primary_button_text_color"]
                ),
                "secondary_button_text_color": request.POST.get(
                    "secondary_button_text_color", DEFAULT_THEME["secondary_button_text_color"]
                ),
            }
            theme = _session_theme(request)
        elif action == "clear_history":
            request.session["analysis_history"] = []
            history = []
        elif action == "open_history":
            history_index = request.POST.get("history_index")
            try:
                idx = int(history_index or "-1")
                curr_history = request.session.get("analysis_history", history)
                if 0 <= idx < len(curr_history):
                    selected_history = curr_history[idx]
            except Exception:
                selected_history = None
        elif action == "save_current_report":
            latest = request.session.get("latest_result")
            if latest and request.user.is_authenticated:
                try:
                    SavedReport.objects.create(
                        user=request.user,
                        title=latest.get("title", "Saved Report"),
                        analysis_type=latest.get("analysis_type", "unknown"),
                        symbol=latest.get("symbol", ""),
                        duration_seconds=float(latest.get("duration_seconds", 0.0)),
                        agent_type=latest.get("agent_type", "adk_agentic"),
                        markdown_report=latest.get("report", ""),
                    )
                except Exception:
                    pass
        elif action == "toggle_pin" and request.user.is_authenticated:
            report_id = request.POST.get("report_id")
            if report_id:
                try:
                    report = SavedReport.objects.get(id=int(report_id), user=request.user)
                    report.is_pinned = not report.is_pinned
                    report.save(update_fields=["is_pinned"])
                except Exception:
                    pass
        elif action == "delete_report" and request.user.is_authenticated:
            report_id = request.POST.get("report_id")
            if report_id:
                try:
                    report = SavedReport.objects.get(id=int(report_id), user=request.user)
                    report.delete()
                    if selected_saved and selected_saved.id == int(report_id):
                        selected_saved = None
                except Exception:
                    pass
        else:
            active_tab = action
            try:
                endpoint, payload, title = _payload_from_action(action, request.POST)
                payload = _apply_model_settings(payload, settings)
                started = time.time()
                result = call_backend(settings["api_url"], endpoint, payload)
                elapsed = round(time.time() - started, 2)

                entry = {
                    "title": title,
                    "type": endpoint,
                    "duration": elapsed,
                    "report": result.get("report", "No report available"),
                    "agent_type": result.get("agent_type", "adk_agentic"),
                }
                history = [entry] + history
                request.session["analysis_history"] = history[:20]
                request.session["latest_result"] = {
                    "title": title,
                    "analysis_type": endpoint,
                    "symbol": result.get("symbol", ""),
                    "duration_seconds": result.get("duration_seconds", elapsed),
                    "agent_type": result.get("agent_type", "adk_agentic"),
                    "report": result.get("report", "No report available"),
                }

                if request.user.is_authenticated:
                    SavedReport.objects.create(
                        user=request.user,
                        title=title,
                        analysis_type=endpoint,
                        symbol=result.get("symbol", ""),
                        duration_seconds=float(result.get("duration_seconds", 0.0)),
                        agent_type=result.get("agent_type", "adk_agentic"),
                        markdown_report=result.get("report", ""),
                    )
            except Exception as exc:
                error = str(exc)

    saved_reports = []
    if request.user.is_authenticated:
        saved_reports = list(
            SavedReport.objects.filter(user=request.user).order_by("-is_pinned", "-created_at")[:30]
        )

    return render(
        request,
        "analyzer/index.html",
        {
            "settings": settings,
            "theme": theme,
            "result": result,
            "error": error,
            "active_tab": active_tab,
            "history": request.session.get("analysis_history", history),
            "saved_reports": saved_reports,
            "selected_saved": selected_saved,
            "selected_history": selected_history,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return render(request, "analyzer/login.html", {"already": True})

    error = None
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return render(request, "analyzer/login.html", {"success": True})
    elif request.method == "POST":
        error = "Invalid username or password"

    return render(request, "analyzer/login.html", {"form": form, "error": error})


def register_view(request):
    if request.user.is_authenticated:
        return render(request, "analyzer/register.html", {"already": True})

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return render(request, "analyzer/register.html", {"success": True})

    return render(request, "analyzer/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return render(request, "analyzer/login.html", {"logged_out": True})


@login_required
def download_report(request, report_id: int):
    try:
        report = SavedReport.objects.get(id=report_id, user=request.user)
    except SavedReport.DoesNotExist as exc:
        raise Http404("Report not found") from exc

    filename = f"{report.analysis_type}_{report.id}.md"
    response = HttpResponse(report.markdown_report, content_type="text/markdown; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
