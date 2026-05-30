# Herramienta de Análisis Fundamental (Bajo Nivel)

## Propósito
- Generar un reporte enfocado en fundamentales a partir de estados financieros (ingresos, balance, flujo de caja) con ratios y narrativa.
- Usada como análisis autónomo y dentro de flujos combinados (técnico + fundamental).

## Datos y Fuentes
- Fundamentals de Yahoo Finance vía `yfinance` (financials, balance sheet, cash flow).
- El parámetro `period` controla años de historial (p. ej., 3y, 5y, 1y).

## Qué Produce
- Reporte en markdown que resume ingresos, márgenes, rentabilidad, apalancamiento, liquidez y flujos de caja.
- Ratios clave (P/E, P/B, ROE, ROA, Current Ratio, Debt/Equity, etc.).
- Fortalezas, riesgos y una recomendación general.

## Implementación en este Repo
- Herramienta MCP: `generate_fundamental_analysis_report` (alias `fundamental_analysis`) en `server/strategies/fundamental_analysis.py` (registrada en `server/main.py`).
- Wrapper Smolagents: `fundamental_analysis_report` en `stock_analyzer_bot/tools.py` (disponible para ambos agentes).
- FastAPI: `/fundamental` (ambos tipos de agente) y `/combined` (emparejado con técnico) usan esta herramienta.
- Streamlit: la pestaña Fundamental usa `/fundamental`; la pestaña Combined usa `/combined` para fusionar técnico + fundamental.

## Parámetros Clave
- `symbol`: ticker (requerido).
- `period`: años de datos a extraer (por defecto 3y).

## Uso Rápido
- Llamada wrapper: `fundamental_analysis_report(symbol="MSFT", period="3y")`.
- FastAPI: `POST /fundamental` o `POST /combined` (con `technical_period` y `fundamental_period`).

## Cuándo Usar
- Cuando se necesita una vista solo de fundamentales con ratios y narrativa en una llamada.
- Como pierna fundamental del flujo combinado (técnico + fundamental).
