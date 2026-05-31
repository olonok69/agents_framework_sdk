# 📊 Stock Analyzer Bot

La **capa de orquestación con ADK** del proyecto MCP Financial Markets Analysis Tool. Este módulo ejecuta el pipeline multiagente en producción usado por el backend FastAPI.

---

## 🎯 Descripción General

Ruta de producción actual:

| Capa | Implementación | Propósito |
|------|----------------|-----------|
| **Runtime API** | `api.py` | Endpoints FastAPI para rutas de análisis/estrategia |
| **Pipeline Agentic** | `adk_bot.py` | Flujo orchestrator + specialist + critic + reporter |
| **Integración MCP** | `mcp_tools.py`, `mcp_client.py` | Llamadas determinísticas y gestión de sesión |
| **Exports de compatibilidad** | `main.py` | Reexporta runners ADK |

Los archivos legacy de smolagents pueden existir como referencia histórica, pero no son la ruta activa del runtime.

---

## 📁 Estructura del Módulo

```
stock_analyzer_bot/
├── __init__.py              # Inicialización del paquete
├── adk_bot.py               # Pipeline ADK multiagente + guardrails
├── adk_bridge.py            # Helpers de integración ADK
├── main.py                  # Exportaciones de compatibilidad ADK
├── api.py                   # Endpoints FastAPI
├── mcp_tools.py             # Wrappers MCP usados por ADK
├── mcp_client.py            # Gestión de sesión MCP
└── README_ES.md             # Este archivo
```

---

## 🤖 Pipeline ADK

El pipeline ADK en `adk_bot.py` ejecuta estas etapas:

1. **Orchestrator** crea el plan de análisis.
2. **Financial specialist** interpreta salida MCP con grounding numérico.
3. **Critic/guardrail** detecta claims no soportados y riesgos.
4. **Reporter** genera el markdown final.
5. **Post-check validator** aplica el contrato de taxonomía (`analysis` vs `strategy`) y puede reescribir/bloquear salidas inválidas.

---

## 🔧 Acceso a Herramientas MCP

`mcp_tools.py` contiene wrappers normalizados usados por ADK.

- Cada wrapper llama una herramienta MCP nominal con parámetros tipados.
- Los errores se capturan y retornan con formato consistente.
- Varias rutas API combinan narrativa ADK y salida MCP raw para exponer `timeseries`.

---

## 📡 Endpoints API

`api.py` expone rutas FastAPI de análisis y estrategia y enruta solicitudes a `adk_bot.py`.

### Configuración

```python
# Variables de entorno
DEFAULT_MODEL_ID = os.getenv("ADK_MODEL_ID", "gpt-4.1")
DEFAULT_MODEL_PROVIDER = os.getenv("ADK_MODEL_PROVIDER", "openai")
DEFAULT_AGENT_TYPE = "adk_agentic"
```

### Endpoints

#### Health Check

```http
GET /health
```

#### Análisis Técnico

```http
POST /technical
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1y",
  "technical_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic",
  "model_id": "gpt-4.1"
}
```

Usa herramientas técnicas MCP + pipeline ADK multiagente.

Controles de modo/riesgo:
- `technical_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Escáner de Mercado

```http
POST /scanner
Content-Type: application/json

{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y",
  "scanner_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Usa herramientas de scanner MCP + síntesis/criticado ADK.

Controles de modo/riesgo:
- `scanner_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Análisis Fundamental

```http
POST /fundamental
Content-Type: application/json

{
  "symbol": "MSFT",
  "period": "3y",
  "agent_type": "adk_agentic"
}
```

Usa `fundamental_analysis_report` con más de 70 aliases para extracción robusta de datos.

#### Análisis Multi-Sector

```http
POST /multisector
Content-Type: application/json

{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"}
  ],
  "period": "1y",
  "multisector_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Usa ensamblado MCP por sector + reporting ADK.

Controles de modo/riesgo:
- `multisector_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Análisis Combinado

```http
POST /combined
Content-Type: application/json

{
  "symbol": "TSLA",
  "technical_period": "1y",
  "fundamental_period": "3y",
  "technical_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Combina análisis técnico y fundamental en una tesis unificada.

Controles de modo/riesgo:
- `technical_mode` (rama técnica): `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### TRIN Breadth (Arms Index)

```http
POST /trin
Content-Type: application/json

{
  "period": "6mo",
  "window": 20,
  "band_k": 1.5,
  "use_log": true,
  "agent_type": "adk_agentic"
}
```

#### Overnight Gaps / Midnight Returns

```http
POST /overnight_gaps
Content-Type: application/json

{
  "symbol": "AAPL",
  "lookback_days": 120,
  "min_gap_pct": 1.0,
  "agent_type": "mcp_tool"
}
```

### Formato de Respuesta

Todos los endpoints devuelven:

```json
{
  "report": "# AAPL Comprehensive Technical Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 35.2,
  "agent_type": "adk_agentic",
  "tools_approach": "MCP tools + ADK multi-agent review"
}
```

Para rutas con modo (`/technical`, `/scanner`, `/multisector`, rama técnica de `/combined`),
el reporte comienza con una línea de metadatos determinística, por ejemplo:

- `> Mode used: Technical=strategy | risk=balanced`
- `> Mode used: Scanner=score | risk=aggressive`

---

## 🧪 Ejemplos de Uso

### CLI

```bash
python -m stock_analyzer_bot.main AAPL --mode technical --period 1y
python -m stock_analyzer_bot.main "AAPL,MSFT" --mode scanner
python -m stock_analyzer_bot.main MSFT --mode fundamental
```

### cURL

```bash
# Technical (ADK runtime)
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "technical_mode": "strategy", "risk_profile": "balanced", "agent_type": "adk_agentic"}'

# Scanner (ADK runtime)
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT", "scanner_mode": "score", "risk_profile": "aggressive", "agent_type": "adk_agentic"}'

# Multi-sector (ADK runtime)
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Banking", "symbols": "JPM,BAC,WFC"},
      {"name": "Tech", "symbols": "AAPL,MSFT,GOOGL"}
    ],
    "multisector_mode": "strategy",
    "risk_profile": "conservative",
    "agent_type": "adk_agentic"
  }'
```

---

## 🛠️ Solución de Problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| "MCP server not found" | Ruta del servidor incorrecta | Verifica que exista `server/main.py` |
| "Connection refused" | FastAPI no está corriendo | Inicia `uvicorn stock_analyzer_bot.api:app --port 8000` |
| "Timeout" | Demasiadas acciones / datos lentos | Reduce alcance o aumenta timeout |
| "Guardrail blocked" | Violación de taxonomía o grounding | Revisa salida MCP y contrato de taxonomía |

---

## 📚 Documentación Relacionada

- [README raíz](../README.md)
- [README del servidor](../server/README.md)
- [Catálogo Analysis vs Strategy](../docs/analysis_strategy_catalog.md)
- [Diagrama de arquitectura ADK](../docs/architecture_adk.svg)

---

<p align="center">
  <i>Stock Analyzer Bot – Runtime ADK + MCP + FastAPI</i>
</p>


## Referencia sobre Prompt Hacking
- https://learnprompting.org/docs/prompt_hacking/introduction
