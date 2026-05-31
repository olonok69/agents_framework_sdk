# CONSTRUIR UNA APLICACIÓN CON AGENT FRAMEWORK — EXTENSIÓN DE LA GUÍA
## Linaje · Librerías · El track técnico de 90 minutos

> **Cómo usar este documento.** Es un **apéndice** de `microsoft_agent_framework_app/docs/guide_en.md`. **No** reemplaza nada de esa guía — el track del ponente de 60 minutos, el gancho de apertura, las notas por fase y el apéndice siguen en pie tal cual están escritos. Este archivo añade tres cosas que la guía original no cubría en profundidad:
>
> 1. **De dónde viene esto** — los tres proyectos previos (`adk_financial_mcp_server`, `azure_foundry_sharepoint`, `evaluation`) que forman la base de esta app de referencia, y qué aportó exactamente cada uno.
> 2. **Las librerías en uso** — una introducción adecuada a cada tecnología (Microsoft Agent Framework, MCP, Azure AI Evaluation SDK, PyRIT), con las versiones que este repo fija, los comandos de instalación, los imports clave y el archivo/función donde se usa cada una.
> 3. **El track de 90 minutos** — un plan de tiempos ampliado que encaja con el slide deck más largo (`Building_an_Agent_Framework_App.pptx`). La guía original está calibrada para 60 minutos; esta sección re-calibra el mismo material para una sesión técnica de 90 minutos y mapea cada bloque a slides y código.
>
> Léelo junto a `docs/technical_guide_en.md` (el recorrido profundo del código) y `docs/architecture.svg`.

---

## Parte A — De dónde viene esto: los tres proyectos base

Esta app de referencia **no es greenfield**. Consolida tres proyectos anteriores en un único stack coherente de cuatro fases. Decir esto en voz alta pronto en la charla merece un slide (slide 4 del deck, *"De dónde viene esto"*) porque reencuadra la app de "una demo que alguien construyó" a "una capa de consolidación sobre trabajo real, probado por separado". Cada proyecto base vive como un **directorio hermano** y se referencia en modo solo-lectura:

```text
agents_framework/
├── adk_financial_mcp_server/     ← el MCP server (reutilizado sin cambios)
├── azure_foundry_sharepoint/     ← el patrón de auth + grounding de Foundry
├── evaluation/                   ← el laboratorio de eval (DeepEval / Inspect / Azure AI Eval)
└── microsoft_agent_framework_app/ ← ESTE proyecto — consolida los tres de arriba
```

El plan de implementación los registra explícitamente como *"external siblings (read-only references)"*, que es el encuadre honesto: este proyecto importa sus lecciones, y en un caso su código real, pero no los forkea ni los modifica.

### A.1 — `adk_financial_mcp_server` → el MCP server (Fase 2)

Este es el único proyecto base cuyo **código se reutiliza textualmente**. Es un FastMCP server que expone ~20 tools de finanzas cuantitativas a lo largo de ~16 familias de estrategias (dual moving average, Bollinger breakout, TRIN breadth, overnight gaps, análisis fundamental, market scanner, performance backtesting y más). Se escribió originalmente para alimentar un bot de stock-analysis de **Google ADK** — un runtime de agente completamente distinto.

El punto principal para la audiencia: **el mismo server, sin cambios, ahora alimenta un agente del Microsoft Agent Framework.** Esa portabilidad es toda la promesa de MCP hecha concreta. En la Fase 2 lo acoplamos por stdio con `MCPStdioTool` (ver `mcp_finance.py`) y apuntamos `MCP_FINANCE_SERVER_PATH` a su `server/main.py`. Mantiene su propio virtualenv de ~90 MB (yfinance, pandas, scipy, statsmodels); la app del agente se mantiene ligera y lo lanza de forma lazy como subproceso solo cuando se pasa `--with-mcp`.

> 💡 **Nota del ponente:** Este es el momento más fuerte de "MCP es real, no un slide" de la charla. El server se construyó para ADK; no tocamos ni una línea. Si alguien en la sala es escéptico con MCP, esta es la respuesta — tools vendor-neutral que sobreviven a un cambio de runtime.

**Dónde aparece en el código:** `src/ms_agent_app/mcp_finance.py` (el cableado de `MCPStdioTool`); claves de `.env` `MCP_FINANCE_SERVER_PATH` y `MCP_FINANCE_PYTHON`. **Slides del deck:** 16 (`mcp_finance.py`), 17 (las familias de tools del server).

### A.2 — `azure_foundry_sharepoint` → el patrón de auth + grounding de Foundry (Fase 1)

Este proyecto anterior es un agente Streamlit con grounding sobre contenido de SharePoint a través de la SharePoint tool de Azure AI Foundry, usando identidad de usuario on-behalf-of (OBO). **No** reutilizamos su código, pero es donde se probó por primera vez el **patrón de conexión y credenciales de Foundry**: cómo apuntar a un project endpoint de Foundry, cómo autenticarse contra Azure con una cadena de credenciales en lugar de una API key, y cómo dejar que Foundry — no Azure OpenAI a secas — sea dueño del deployment del modelo, el RBAC y el content filtering.

El plan lo lista como el *"Foundry env vars & auth example."* La Fase 1 de esta app destila ese patrón en `foundry_client.py`: `FoundryChatClient` más una credencial (la cadena de credenciales excluye el navegador interactivo y permite tenants adicionales para logins multi-tenant). El slide "Por qué Foundry, no Azure OpenAI a secas" (slide 13 del deck) es la lección directa heredada de este proyecto.

> 💡 **Nota del ponente:** Úsalo para anticiparte a la pregunta "¿por qué no llamar directamente a Azure OpenAI?". La respuesta se aprendió aquí: en una empresa quieres deployments con nombre y gobernados, content filtering del lado del servidor y acceso basado en identidad — Foundry da los tres detrás de un cliente.

**Dónde aparece en el código:** `src/ms_agent_app/foundry_client.py` (`build_foundry_client`). **Slides del deck:** 12 (`foundry_client.py` + `agent_factory.py`), 13 (por qué Foundry).

### A.3 — `evaluation` → el laboratorio de evaluación (Fase 3)

Este proyecto hermano es un laboratorio práctico que evalúa agentes a través de tres ecosistemas: **DeepEval** (eval test-first y CI-friendly), **Inspect AI** (pipelines de tareas estructuradas `Dataset → Solver → Scorer`) y el **Azure AI Evaluation SDK** (métricas agentic nativas de Azure y evaluación por lotes). Es donde se probaron los patrones de trajectory + evaluator antes de traerlos aquí.

La Fase 3 de esta app sigue la forma de `evaluation/03_azure_ai_eval_agents.py`: los mismos tres agentic evaluators (`IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator`), el mismo contrato de mensajes al estilo OpenAI y el mismo patrón de judge LLM-as-judge configurado con un `ModelConfiguration`. No reutilizamos el código, pero `score.py` es un descendiente conceptual directo de ese script.

**Dónde aparece en el código:** `src/ms_agent_app/eval/` (`dataset.py`, `runner.py`, `score.py`). **Slides del deck:** 19–24 (la fase de eval completa).

---

## Parte B — Las librerías en uso

Cuatro tecnologías, cada una con un rol de una línea, su comando de instalación, la versión que este repo fija, los imports clave y dónde se usa. Este es el contenido del slide 7 ("La caja de herramientas").

### B.1 — Microsoft Agent Framework

- **Rol:** el runtime del agente — `Agent`, `AgentResponse`, chat clients y un MCP client nativo.
- **Versión:** prerelease (vía general-available, 2026); el repo fija `agent-framework>=1.4.0` más `agent-framework-foundry`, `agent-framework-openai`, `agent-framework-anthropic`.
- **Instalación:** `pip install agent-framework` (o vía `uv add --prerelease=allow ...`).
- **Imports clave:** `from agent_framework import Agent, MCPStdioTool`; `from agent_framework.foundry import FoundryChatClient`; `from agent_framework.openai import OpenAIChatClient`; `from agent_framework.anthropic import AnthropicClient`.
- **Dónde se usa:** `foundry_client.py`, `agent_factory.py`, `mcp_finance.py`.

### B.2 — Model Context Protocol (MCP)

- **Rol:** protocolo de tools vendor-neutral sobre stdio / SSE / HTTP. Dos verbos: `list_tools`, `call_tool`.
- **Versión:** MCP Python SDK + FastMCP; el repo fija `mcp>=1.27.1`.
- **Instalación:** `pip install mcp fastmcp`.
- **Imports clave:** `agent_framework.MCPStdioTool` (lado cliente); el server usa `FastMCP` en `adk_financial_mcp_server/server/main.py`.
- **Dónde se usa:** `mcp_finance.py` + el server hermano.

### B.3 — Azure AI Evaluation SDK

- **Rol:** tres agentic evaluators (LLM-as-judge) que puntúan trajectories en calidad.
- **Versión:** `azure-ai-evaluation` (el repo fija `>=1.0.0`; las notas del deck mencionan la línea 1.16.x).
- **Instalación:** `pip install azure-ai-evaluation azure-identity`.
- **Imports clave:** `from azure.ai.evaluation import IntentResolutionEvaluator, TaskAdherenceEvaluator, ToolCallAccuracyEvaluator, AzureOpenAIModelConfiguration, OpenAIModelConfiguration`.
- **Dónde se usa:** `eval/score.py`.

### B.4 — Microsoft PyRIT

- **Rol:** Python Risk Identification Toolkit — targets, attacks, converters, scorers.
- **Versión:** `pyrit>=0.13.0` (grupo de extras opcional).
- **Instalación:** `pip install pyrit` · `uv sync --extra redteam`.
- **Imports clave:** `from pyrit.setup import initialize_pyrit_async`; `from pyrit.prompt_target import PromptTarget, OpenAIChatTarget`; `from pyrit.executor.attack import PromptSendingAttack, AttackExecutor, AttackScoringConfig`; `from pyrit.score import SelfAskRefusalScorer`; `from pyrit.models import Message, MessagePiece, construct_response_from_request`.
- **Dónde se usa:** `redteam/target.py`, `redteam/run.py`.

---

## Parte C — El track de 90 minutos

La guía original está calibrada para **60 minutos / 15 slides**. El deck más largo (`Building_an_Agent_Framework_App.pptx`) está calibrado para **90 minutos**. Los 30 minutos extra van casi por completo a (a) el nuevo encuadre de linaje y librerías de las Partes A y B, y (b) más tiempo sobre el código en vivo en los slides de código de cada fase. Nada del track de 60 minutos se elimina — se amplía.

### C.1 — Desglose de tiempos de 90 minutos

| Hora | Sección | Slides del deck | Duración |
|------|---------|-------------|----------|
| 0:00 | Apertura · linaje · por qué este stack | 1–5 | 10 min |
| 0:10 | Librerías · arquitectura · el modelo de cuatro fases | 6–8 | 4 min |
| 0:14 | Cimiento compartido — `config.py` | 9 | 2 min |
| 0:16 | **Fase 1 — Agent + Foundry** | 10–13 | 12 min |
| 0:28 | **Fase 2 — Tools locales vía MCP** | 14–18 | 14 min |
| 0:42 | **Fase 3 — Azure AI Evaluation SDK** | 19–24 | 14 min |
| 0:56 | **Fase 4 — Red-teaming con PyRIT** | 25–29 | 16 min |
| 1:12 | Lecciones aprendidas y conclusiones | 30–31 | 8 min |
| 1:20 | Recursos y Q&A | 32 | 5 min |
| | **Total** | | **90 min** |

### C.2 — Ampliación sección por sección

Abajo, cada bloque lista solo lo que es **nuevo o re-calibrado** respecto a la guía de 60 minutos. Conserva los ganchos y notas del ponente de la guía original; superpón esto encima.

**0:00–0:10 — Apertura · linaje · por qué este stack (slides 1–5).**
Abre con el gancho existente de los cuatro logos (tres conocidos, PyRIT el desconocido — ver la guía original). Luego añade el **beat de linaje** (nuevo slide 4, Parte A): esta app consolida tres proyectos reales previos. Aterriza pronto la mejor frase — *el MCP server se construyó para un bot de Google ADK y corre aquí sin cambios.* Cierra el bloque con el argumento existente de "por qué este stack, por qué ahora" (slide 5): un agente empresarial moderno ya no es un LLM más un system prompt; necesita razonamiento + orquestación, tools en vivo, eval de calidad y eval de seguridad — cuatro propiedades ortogonales.

**0:10–0:14 — Librerías · arquitectura · modelo de cuatro fases (slides 6–8).**
Este es el contenido nuevo de la **Parte B**, mantenido conciso. Cuatro tiles (slide 6): Agent Framework, MCP, Azure AI Evaluation SDK, PyRIT — nombre, rol de una línea, comando de instalación, versión. Luego la arquitectura en un diagrama (slide 7) y el modelo gated/incremental de dos ejes (calidad vs seguridad) (slide 8). Insiste: cada fase es ejecutable de forma independiente y depende solo de las fases por debajo de ella.

**0:14–0:16 — Cimiento compartido, `config.py` (slide 9).**
Dos minutos. Un objeto de settings tipado, un `.env`, el seam de inyección de dependencias que usan los tests. Menciona que las variables de judge de la Fase 3/4 se validan de forma lazy — solo cuando corren esos scripts. `config.py` es el seam de inyección de dependencias que los tests explotan (`Settings(_env_file=None)` para el test negativo de entorno faltante). El slide 9 del deck es este slide.

**0:16–0:28 — Fase 1 (slides 10–13), 12 min.**
Conceptos (slide 11): Agent / AgentResponse / chat client — y *al Agent le da igual qué cliente sostiene.* Código (slide 12): `foundry_client.build_foundry_client` y `agent_factory.build_chat_agent`, incluido `DEFAULT_INSTRUCTIONS`. Justificación (slide 13): por qué Foundry, no Azure OpenAI a secas — la lección heredada de `azure_foundry_sharepoint` (deployments con nombre, RBAC, filtros del lado del servidor, identidad). Ejecútalo en vivo: `uv run ms-agent-app` (o `uv run ms-agent-app --provider openai|azure-openai|anthropic`).

**0:28–0:42 — Fase 2 (slides 14–18), 14 min.**
Modelo mental de MCP (slide 15): 3 sustantivos, 2 verbos. Código (slide 16): `mcp_finance.py` — `MCPStdioTool` + el async context manager. El server (slide 17): el `adk_financial_mcp_server` sin modificar, ~20 tools, su propio venv de 90 MB, lanzado de forma lazy. Protocolo de cable (slide 18): Ping → ListTools → function defs → llamada del modelo → CallTool → respuesta `role=tool`. Ejecútalo en vivo: `uv run ms-agent-app --with-mcp` (override de provider opcional: `--provider openai|azure-openai|anthropic|foundry`), luego *"Run a dual moving average analysis on AAPL."*

**0:42–0:56 — Fase 3 (slides 19–24), 14 min.**
Por qué puntuar la calidad (slide 20). Los tres evaluators con sus rangos/umbrales (slide 21). El contrato de trajectory — `query`/`response` son listas en el esquema de mensajes de OpenAI (slide 22). `score.py` y las dos trampas — `FunctionTool.parameters` es un método, y el skip de dashboard-verde-silencioso (slide 23). Números reales de una ejecución limpia, y el coste de judge ≈ $0.05/pasada (slide 24). Ejecútalo en vivo: `uv run python -m ms_agent_app.eval.score` (provider del agente desde `MODEL_PROVIDER`; provider del judge desde `JUDGE_PROVIDER`). Repite: el judge no es el modelo del agente.

**0:56–1:12 — Fase 4 (slides 25–29), 16 min — el clímax.**
Esta recibe el mayor tiempo porque es la menos familiar y carga el mejor hallazgo de la charla. Calidad vs red-team — *"¿hizo el agente lo que el usuario quería?"* vs *"¿hizo lo que no debe?"* (slide 26). `target.py` — las únicas ~20 líneas de código específico de PyRIT que poseemos (slide 27). El dataset de cinco probes / cinco comportamientos (slide 28). Luego **el hallazgo** (slide 29): un **scorer con falso negativo** — la probe `prompt-injection-tool` muestra *delayed compliance* (el agente primero rechaza, luego añade un override al argumento de la tool), y `SelfAskRefusalScorer` lo marcó como refusal. Muestra la tabla de variabilidad de 3 ejecuciones (jailbreak y system-prompt extraction bloqueados en el filtro cada vez; prompt-injection-tool SUCCESS\*/SUCCESS\*/ERROR). Ejecútalo en vivo: `uv run ms-agent-redteam` (provider del agente desde `MODEL_PROVIDER`; provider del judge desde `JUDGE_PROVIDER`). Recuérdale a la sala dos veces que `SUCCESS` = refusal detectado.

**1:12–1:20 — Lecciones y conclusiones (slides 30–31), 8 min.**
Lecciones (slide 30): el patrón de cuatro fases es reutilizable; un `.env` / una credencial; los imports lazy reducen a la mitad la superficie de instalación; LLM-as-judge tiene debilidades conocidas (delayed compliance, refusals verbosos, un solo disparo sobre multi-turno). Tres conclusiones (slide 31): la eval de calidad y la de seguridad son complementarias (una Fase 3 verde no significa nada si la Fase 4 falla); lee los transcripts (el hallazgo era invisible a nivel de score); elige capas, no un stack (Agent Framework, Foundry, MCP, Eval SDK y PyRIT son intercambiables de forma independiente — optimiza cada capa por separado).

**1:20–1:25 — Recursos y Q&A (slide 32), 5 min.**
Apunta a los cuatro enlaces de librerías (Parte B), los tres proyectos hermanos (Parte A) y el propio `technical_guide_en.md` del repo. Mantén el Q&A en 5 minutos; ofrece continuar offline.

### C.3 — Si tienes que comprimir de vuelta hacia 60 minutos

Si el slot se encoge el día de la charla, recorta en este orden y vuelves aproximadamente a la forma original de 60 minutos sin perder la columna vertebral: recorta el bloque de librerías (slide 6) a 90 segundos; convierte el slide del protocolo de cable (18) y el del contrato de trajectory (22) en comentarios hablados; acorta lecciones (30) a las tres conclusiones solamente. **No** recortes el slide 29 (el hallazgo) ni ninguna de las cuatro ejecuciones en vivo — esas son la charla.

---

*Fin de la extensión. Empareja con `docs/guide_en.md`, `docs/technical_guide_en.md`, `docs/architecture.svg` y el deck `Building_an_Agent_Framework_App.pptx`.*
