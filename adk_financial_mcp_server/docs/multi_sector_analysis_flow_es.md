# Flujo de Análisis Multisector

## Propósito
- Comparar múltiples sectores escaneando símbolos dentro de cada sector y luego ordenando sectores y acciones.
- Destaca liderazgo, amplitud de señales de compra y listas de evitar entre sectores.

## Cómo Funciona
- Ruta ToolCallingAgent: por sector llama la herramienta de alto nivel `market_scanner` (escáner unificado) y agrega resultados.
- Ruta CodeAgent: bucles anidados sector → acciones → cuatro estrategias de bajo nivel, luego agrega señales y rankings en Python.

## Implementación en este Repo
- Endpoint FastAPI: `POST /multisector` en `stock_analyzer_bot/api.py`.
- Pestaña Streamlit: "🌐 Multi-Sector Analysis" en `streamlit_app.py` con sectores predeterminados; soporta CodeAgent para velocidad.
- Prompt de CodeAgent: `MULTI_SECTOR_PROMPT` en `stock_analyzer_bot/main_codeagent.py`.

## Entradas
- `sectors`: lista de `{name, symbols}` (tickers separados por comas por sector).
- `period`: ventana técnica (por defecto 1y).
- `agent_type`: `tool_calling` o `code_agent`; `executor_type` para CodeAgent.

## Salidas
- Markdown con ranking de sectores, mejores acciones por sector, picks/avoid y tablas de resumen.
- Usa las cuatro estrategias técnicas de bajo nivel (o el escáner de alto nivel por sector en modo tool-calling).

## Uso Rápido
- FastAPI: `POST /multisector` con arreglo de sectores, periodo y agent_type.
- Streamlit: formulario de la pestaña Multi-Sector.
