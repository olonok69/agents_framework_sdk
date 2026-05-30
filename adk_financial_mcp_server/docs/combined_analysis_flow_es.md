# Análisis Combinado Técnico + Fundamental (API / Flujo de Agente)

## Propósito
- Generar un reporte único que mezcla análisis técnico (4 estrategias) con análisis fundamental en una sola llamada.
- Entrega una tesis balanceada: timing + calidad de la empresa.

## Cómo Funciona
- Lado técnico: ejecuta las cuatro estrategias de bajo nivel (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual MA) vía CodeAgent o vía la herramienta integral de alto nivel (ruta ToolCallingAgent).
- Lado fundamental: extrae estados financieros y ratios vía la herramienta de análisis fundamental.
- El agente une ambos en un markdown unificado con recomendaciones.

## Implementación en este Repo
- Endpoint FastAPI: `POST /combined` en `stock_analyzer_bot/api.py`.
  - Ruta ToolCallingAgent: llama `comprehensive_performance_report` (técnico) + `fundamental_analysis_report` (fundamental) en dos llamadas MCP.
  - Ruta CodeAgent: llama las cuatro herramientas técnicas de bajo nivel + `fundamental_analysis_report` vía orquestación en Python.
- Pestaña Streamlit: "🔄 Combined Analysis" en `streamlit_app.py`, con periodos configurables para técnico y fundamental.
- Prompt de CodeAgent: `COMBINED_ANALYSIS_PROMPT` en `stock_analyzer_bot/main_codeagent.py`.

## Parámetros Clave
- `symbol` (requerido).
- `technical_period` (por defecto 1y).
- `fundamental_period` (por defecto 3y).
- `agent_type`: `tool_calling` o `code_agent`; `executor_type` para CodeAgent.

## Salidas
- Reporte en markdown con resumen ejecutivo, aspectos técnicos por estrategia, puntos fundamentales y una recomendación combinada.

## Uso Rápido
- FastAPI: `POST /combined` con símbolo, periodos y agent_type.
- Streamlit: formulario de la pestaña Combined.
