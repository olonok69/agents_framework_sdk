# GUÍA TÉCNICA — ms-agent-app
## Recorrido profundo del código: Agent Framework · Foundry · MCP · Azure AI Evaluation · PyRIT

> Documento complementario de `docs/guide_en.md` (la guía del ponente) y `docs/guide_en_extension.md` (linaje, librerías y el track de 90 minutos). Mientras que la guía del ponente está calibrada para presentar, esta guía técnica recorre el código módulo a módulo: imports clave, clases y métodos a explicar, trampas de implementación y cuándo usar cada patrón. Léela junto a `docs/architecture.svg`.

---

## 1. Introducción

`ms-agent-app` es una aplicación Python de ~30 archivos que conecta cuatro capas de un stack de agentes moderno y luego demuestra que funciona en dos ejes ortogonales (calidad y seguridad). Este documento es el recorrido del código; explica cada módulo bajo `src/ms_agent_app/` con suficiente detalle como para extender el proyecto o adaptarlo a un agente real.

El stack en una frase: **un chat agent del Agent Framework respaldado por Foundry, con tools locales vía un subproceso MCP conforme al estándar, scoring de calidad consciente de la trajectory mediante tres evaluators LLM-as-judge del Azure AI Evaluation SDK, y probing adversarial con PyRIT a través de un adaptador de target de 20 líneas — donde los modos de fallo del scorer son en sí mismos un momento de aprendizaje.**

Una frase por fase:

- **Fase 1:** "Un runtime de agente vendor-thin respaldado por modelos hospedados en Azure con gobernanza incorporada."
- **Fase 2:** "Tools locales vía un subproceso MCP conforme al estándar — escribe las tools una vez, acóplalas a cualquier framework."
- **Fase 3:** "Scoring de calidad consciente de la trajectory con tres evaluators LLM-as-judge que vienen con Azure."
- **Fase 4:** "Probing adversarial a través de PyRIT con un adaptador de target de 20 líneas, donde los modos de fallo del scorer son en sí mismos un momento de aprendizaje."

Una frase por estilo de programación:

- **Estilo Settings** (`config.py`): "Configuración tipada e inyectada por dependencias, con cero `os.environ` fuera del módulo."
- **Estilo Factory** (`foundry_client.py`, `agent_factory.py`, `mcp_finance.py`): "Builders de dos líneas + async context-managers para el lifecycle."
- **Estilo Adapter** (`redteam/target.py`): "Puentes subclasea-e-implementa-un-método entre frameworks que no se conocen entre sí."
- **Estilo Pipeline** (`eval/score.py`, `redteam/run.py`): "Recopilar → puntuar → persistir, con una separación clara entre la recolección de datos y el juicio."

---

## 2. Configuración y variables de entorno

Todas las variables de entorno se leen en un único sitio (`config.py`). La tabla siguiente resume cada una, qué fase la usa y notas.

| Variable | Usada por | Notas |
|---|---|---|
| `MODEL_PROVIDER` | 1, 2, 3, 4 (chat) | `foundry` (por defecto), `openai`, `azure-openai`, `anthropic` |
| `FOUNDRY_PROJECT_ENDPOINT` | 1, 2, 3, 4 (foundry chat provider) | Requerida cuando `MODEL_PROVIDER=foundry` |
| `FOUNDRY_MODEL_DEPLOYMENT_NAME` | 1, 2, 3, 4 (foundry chat provider) | Nombre del deployment de chat, p. ej. `gpt-4.1` |
| `OPENAI_API_KEY` | 1, 2, 3, 4 (openai chat provider) | Requerida cuando `MODEL_PROVIDER=openai` |
| `OPENAI_CHAT_MODEL` | 1, 2, 3, 4 (openai chat provider) | Clave de modelo preferida |
| `OPENAI_MODEL` | 1, 2, 3, 4 (openai chat provider) | Clave de modelo de fallback |
| `OPENAI_BASE_URL` | 1, 2, 3, 4 (openai chat provider) | Endpoint personalizado opcional |
| `AZURE_OPENAI_ENDPOINT` | 1, 2, 3, 4 (azure-openai chat provider) | Requerida cuando `MODEL_PROVIDER=azure-openai` |
| `AZURE_OPENAI_CHAT_MODEL` | 1, 2, 3, 4 (azure-openai chat provider) | Clave de modelo preferida |
| `AZURE_OPENAI_MODEL` | 1, 2, 3, 4 (azure-openai chat provider) | Clave de modelo de fallback |
| `AZURE_OPENAI_API_KEY` | 1, 2, 3, 4 (azure-openai chat provider) | Opcional con auth de identidad de Azure |
| `AZURE_OPENAI_API_VERSION` | 1, 2, 3, 4 (azure-openai chat provider) | Override opcional de la versión de API |
| `ANTHROPIC_API_KEY` | 1, 2, 3, 4 (anthropic chat provider) | Requerida cuando `MODEL_PROVIDER=anthropic` |
| `ANTHROPIC_CHAT_MODEL` | 1, 2, 3, 4 (anthropic chat provider) | ID del modelo Claude |
| `ANTHROPIC_BASE_URL` | 1, 2, 3, 4 (anthropic chat provider) | Endpoint personalizado opcional |
| `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | 1, 2, 3, 4 (auth) | Recogidas por `DefaultAzureCredential` |
| `MCP_FINANCE_SERVER_PATH` | 2 | Ruta absoluta a `adk_financial_mcp_server/server/main.py` |
| `MCP_FINANCE_PYTHON` | 2 | Intérprete con las deps del MCP server |
| `JUDGE_PROVIDER` | 3, 4 (judge) | `azure-openai` (por defecto) o `openai` |
| `AZURE_DEPLOYMENT_NAME` | 3, 4 (judge, azure-openai) | Deployment del judge model, p. ej. `gpt-4.1-mini` |
| `AZURE_API_KEY` | 3, 4 (judge, azure-openai) | Key de Azure Cognitive Services para el judge |
| `AZURE_ENDPOINT` | 3, 4 (judge, azure-openai) | URL **a nivel de cuenta** — sin sufijo `/api/projects/...` |
| `AZURE_API_VERSION` | 3 (judge, azure-openai) | Por defecto `2024-12-01-preview` |
| `JUDGE_OPENAI_API_KEY` | 3, 4 (judge, openai) | Override opcional; fallback a `OPENAI_API_KEY` |
| `JUDGE_OPENAI_MODEL` | 3, 4 (judge, openai) | Override opcional; fallback a `OPENAI_CHAT_MODEL` / `OPENAI_MODEL` |
| `JUDGE_OPENAI_BASE_URL` | 3, 4 (judge, openai) | Opcional; por defecto `OPENAI_BASE_URL`, luego `https://api.openai.com/v1` |
| `JUDGE_OPENAI_ORGANIZATION` | 3, 4 (judge, openai) | Organización opcional |

> ⚠ Cuando `JUDGE_PROVIDER=azure-openai`, el `AZURE_ENDPOINT` del judge y el `FOUNDRY_PROJECT_ENDPOINT` de Foundry parecen casi idénticos, pero la URL del judge **NO** debe incluir `/api/projects/...`. La ruta de Foundry es para el Agent Service; las llamadas de chat-completion usan la URL de cuenta a secas.

---

## 3. Módulo compartido: `config.py`

### 3.1 Propósito y diseño

`src/ms_agent_app/config.py` es el **único** sitio donde se leen variables de entorno. Cualquier otro módulo recibe una instancia de `Settings` y nunca toca `os.environ`. Esto se impone por revisión, no por el lenguaje.

### 3.2 Imports clave y roles

- `pydantic-settings.BaseSettings` — binding tipado de variables de entorno.
- `pydantic.Field`, `field_validator` — mapeo de alias (`FOUNDRY_PROJECT_ENDPOINT` → `foundry_project_endpoint`), pre-validación de rutas.
- `dotenv.load_dotenv()` — carga explícita de `.env` en tiempo de import para que `Settings()` funcione en scripts.

### 3.3 Decoradores, clases y métodos a explicar

#### Clase: `Settings(BaseSettings)`

Rol:

- Fuente única de configuración tipada.
- Lanza un `ValidationError` claro si falta cualquier variable requerida del provider seleccionado.
- `model_config = SettingsConfigDict(env_file=".env", extra="ignore")` la hace tolerante a variables de entorno no relacionadas (p. ej. credenciales SP, rutas MCP) manteniendo su propia superficie acotada.

Ángulo didáctico:

- Trata `Settings` como el **seam de inyección de dependencias** de toda la app. Los tests usan `monkeypatch.setenv(...)` y un override `_env_file=None` para construir settings deterministas sin tocar `.env`.

#### `@field_validator("mcp_finance_server_path", mode="before")`

Rol:

- Resuelve `~` y rutas relativas a rutas absolutas *antes* de la coerción de tipo a `Path`.
- Devuelve `None` si el valor está vacío, para que las instancias de `Settings` creadas sin variables MCP (Fase 1) sigan validando.

#### Método: `mcp_python(self) -> str`

Rol:

- Devuelve la ruta del intérprete para el subproceso MCP.
- Hace fallback a `sys.executable` si `MCP_FINANCE_PYTHON` no está definido.

Ángulo didáctico:

- La razón real de que exista este método: el MCP server tiene 90+ MB de deps financieras instaladas en su **propio** venv en `/home/$USER/.venvs/mcp-finance-server/`. El venv de nuestra aplicación no. La separación mantiene baja la latencia de la instalación base.

---

## 4. Fase 1 — Agent + Foundry

### 4.1 Propósito y diseño

Hacer bootstrap de un `Agent` del Microsoft Agent Framework ligado a un deployment de modelo de Azure AI Foundry, ejecutable desde un CLI local con manejo de credenciales de una línea.

Archivos:

```
src/ms_agent_app/
├── foundry_client.py       # 25 LOC — builder de FoundryChatClient
├── agent_factory.py        # 32 LOC — builder de Agent con tools opcionales
└── cli.py                  # ~70 LOC — REPL async con flag --with-mcp
```

### 4.2 Imports clave y roles

- `agent_framework.Agent` — contenedor de runtime para un LLM client + instrucciones + tools.
- `agent_framework.foundry.FoundryChatClient` — chat client para un deployment de Azure AI Foundry.
- `azure.identity.DefaultAzureCredential` — cadena de credenciales: SP por env-var → managed identity → `az login` → interactivo.

### 4.3 Clases, métodos y patrones que deberías explicar

#### Clase: `FoundryChatClient`

Rol:

- Adaptador que permite al `Agent` hablar con un deployment de Foundry sobre su superficie de chat-completions.
- Lleva la credencial y el nombre del deployment en cada petición.

Tip de presentación:

- Enfatiza que es uno de varios chat clients de la familia del Agent Framework. `OpenAIChatClient`, `AnthropicChatClient`, `AzureAIChatClient` son hermanos. **La clase `Agent` es agnóstica al cliente.**

#### Clase: `DefaultAzureCredential`

Rol:

- Recorre una cadena de fuentes de credenciales en orden de prioridad: service principal por env-var, managed identity, Azure CLI (`az login`), login de Visual Studio / VS Code, navegador interactivo.

Ángulo didáctico:

- Una sola cadena de credenciales significa que el **mismo código corre en tres modos de despliegue**: portátil local (`az login`), CI (SP por env-var), contenedor (managed identity). Excluimos `InteractiveBrowserCredential` explícitamente para fallar rápido en shells headless:

```python
DefaultAzureCredential(exclude_interactive_browser_credential=True)
```

#### Función: `build_foundry_client(settings) -> FoundryChatClient`

Rol:

- Factory de dos líneas: construye una credencial, pasa tanto la credencial como `project_endpoint`/`model` a `FoundryChatClient`.
- Pre-inyecta `additionally_allowed_tenants` cuando `AZURE_TENANT_ID` está definido, lo que evita fallos de SP entre tenants en organizaciones multi-tenant.

#### Función: `build_chat_client(settings, provider=None) -> ChatClient`

Rol:

- Dispatcher de provider seleccionado por `MODEL_PROVIDER` (o por un `provider=` explícito / el flag `--provider` del CLI).
- Devuelve `FoundryChatClient`, `OpenAIChatClient` (enrutado OpenAI o Azure-OpenAI) o `AnthropicClient` — todos detrás de la misma interfaz que ve el `Agent`.
- `build_foundry_client` / `build_openai_client` / `build_azure_openai_client` / `build_anthropic_client` son los builders por-provider a los que delega.

#### Función: `build_chat_agent(settings, *, provider=None, name, instructions, tools=None) -> Agent`

Rol:

- Envuelve el cliente devuelto por `build_chat_client(settings, provider=provider)` en un `Agent`, nombrándolo `<Provider>Agent`.
- Solo añade `tools` al constructor del Agent cuando los callers realmente los pasan. Este patrón mantiene la superficie de la Fase 1 libre de imports de MCP.

Ángulo didáctico:

- La constante `DEFAULT_INSTRUCTIONS` es la pieza de ingeniería de seguridad/calidad más pequeña y de mayor apalancamiento de toda la app: "prefiere llamar a una tool antes que adivinar… si no puedes responder a partir de los resultados de la tool, dilo claramente". Sube la tool-call accuracy en la Fase 3 y reduce el consejo financiero alucinado que sacan a la luz las probes de la Fase 4.

### 4.4 Sección por sección: `cli.py`

El REPL es deliberadamente minimalista (~70 líneas). Las decisiones interesantes:

#### Import lazy de MCP

```python
async def _chat_loop(settings: Settings, with_mcp: bool) -> int:
    if with_mcp:
        from .mcp_finance import open_finance_mcp_tool  # noqa: PLC0415
        ...
```

Por qué existe:

- El módulo `mcp_finance` importa `agent_framework.MCPStdioTool`, que es un import pesado. Los usuarios que solo necesitan el chat de la Fase 1 no deberían pagar ese coste.
- La instalación base no requiere que la ruta del MCP server esté definida; la Fase 1 igualmente corre.

#### `KeyboardInterrupt` devuelve 130

Convención POSIX: `Ctrl-C` devuelve 128 + SIGINT (2) = 130. Es el tipo de detalle que importa para wrappers de CI que dependen del exit code.

#### Una sola instancia de Agent a través de los turnos

`Agent` y `MCPStdioTool` se entran una vez al inicio de `_chat_loop` y se reutilizan en cada turno del usuario. El subproceso NO se relanza por prompt. Es además la única forma de que el historial de conversación se acumule correctamente entre turnos.

### 4.5 Modelo de runtime

```bash
# Fase 1
uv run ms-agent-app
uv run ms-agent-app --provider foundry
uv run ms-agent-app --provider openai
uv run ms-agent-app --provider azure-openai
uv run ms-agent-app --provider anthropic

# Fase 2
uv run ms-agent-app --with-mcp
uv run ms-agent-app --with-mcp --provider foundry
uv run ms-agent-app --with-mcp --provider openai
uv run ms-agent-app --with-mcp --provider azure-openai
uv run ms-agent-app --with-mcp --provider anthropic

# Fase 3 (el enrutado de provider viene de MODEL_PROVIDER + JUDGE_PROVIDER en .env)
uv run python -m ms_agent_app.eval.score

# Fase 4 (el enrutado de provider viene de MODEL_PROVIDER + JUDGE_PROVIDER en .env)
uv run ms-agent-redteam
```

Flujo de extremo a extremo para un turno:

1. El usuario teclea un prompt.
2. `agent.run(prompt)` serializa el historial de conversación y lo envía a `FoundryChatClient`.
3. `FoundryChatClient` llama al endpoint de chat-completions de Foundry con el bearer token del usuario.
4. La response llega en streaming; se imprime `AgentResponse.text`.

### 4.6 Cuándo usar este patrón

Úsalo cuando:

- Quieres un runtime de agente vendor-thin respaldado por modelos hospedados en Azure con gobernanza incorporada.
- Esperas cambiar de modo de credencial (portátil ↔ CI ↔ contenedor) sin cambios de código.
- Quieres una base que más adelante soporte el Foundry Agent Service (agente gestionado del lado del servidor) sin reescritura del lado del cliente.

---

## 5. Fase 2 — Tools locales vía MCP

### 5.1 Propósito y diseño

Acoplar el `adk_financial_mcp_server` hermano (FastMCP, transporte stdio) al agente a través de `MCPStdioTool`, con un lifecycle async limpio y errores amistosos cuando las variables de entorno están mal.

Archivo:

```
src/ms_agent_app/mcp_finance.py     # 35 LOC — builder + context manager
```

### 5.2 Imports clave y roles

- `agent_framework.MCPStdioTool` — gestiona un subproceso MCP y hace de proxy de `list_tools`/`call_tool` hacia el Agent.
- `contextlib.asynccontextmanager` — envuelve `MCPStdioTool` para un cierre limpio.

### 5.3 Clases, métodos y patrones a explicar

#### Clase: `MCPStdioTool`

Rol:

- Lanza un MCP server como subproceso, abre un canal JSON-RPC bidireccional sobre stdin/stdout y expone las tools del server al Agent.
- Es dueña del lifecycle del subproceso: entra en `async with`, termina al salir.

Atributos importantes (expuestos por nombre):

- `functions: list[FunctionTool]` — las tools descubiertas tras la primera conexión.
  - Cada `FunctionTool` tiene `name: str`, `description: str` y `parameters` (un **método** que devuelve el dict JSON-Schema — no un atributo, ver Fase 3).
- `call_tool(...)` — invocación manual directa (rara vez necesaria; el Agent lo gestiona).
- `is_connected: bool` — útil para sanity checks.

Ángulo didáctico:

- MCP resuelve el problema del que nadie habla: cada framework reinventaba el tool-calling de forma distinta. Usando `MCPStdioTool`, el **mismo finance server en Python** que alimenta la demo de Google ADK en `adk_financial_mcp_server/stock_analyzer_bot/` ahora alimenta nuestra demo del Microsoft Agent Framework, con cero cambios del lado del server.

#### Función: `build_finance_mcp_tool(settings) -> MCPStdioTool`

Rol:

- Lanza `ValueError` si `MCP_FINANCE_SERVER_PATH` no está definido, o `FileNotFoundError` si apunta a un archivo inexistente.
- Devuelve un `MCPStdioTool(name="finance_tools", command=<python>, args=[<server_path>])` configurado — **no** entra en su context async.

Por qué separar construir de entrar:

- Los tests pueden construir uno sin lanzar un subproceso.
- Los callers controlan el lifetime explícitamente vía `async with`.

```python
@asynccontextmanager
async def open_finance_mcp_tool(settings: Settings) -> AsyncIterator[MCPStdioTool]:
    """Async context-manager wrapping MCPStdioTool for clean shutdown."""
    tool = build_finance_mcp_tool(settings)
    async with tool as live:
        yield live
```

---

## 6. Fase 3 — Azure AI Evaluation SDK

### 6.1 Propósito y diseño

Puntuar trajectories reproducidas del agente a lo largo de tres ejes — intent resolution, task adherence y tool-call accuracy — usando LLM-as-judge contra un deployment configurable, y persistir los resultados como JSON.

Archivos:

```
src/ms_agent_app/eval/
├── dataset.py     # 4 EvalCases
├── runner.py      # dataclass Trajectory + traductor AgentResponse → mensajes OpenAI
└── score.py       # entry point: escribe .eval_outputs/results.json
```

### 6.2 Imports clave y roles

De `azure.ai.evaluation`:

- `AzureOpenAIModelConfiguration` / `OpenAIModelConfiguration` — config del judge model (seleccionada por `JUDGE_PROVIDER`).
- `IntentResolutionEvaluator` — Likert 1–5, puntúa cómo de bien la response aborda la intención del usuario.
- `TaskAdherenceEvaluator` — 0.0–1.0, puntúa si la response cumple la tarea del usuario.
- `ToolCallAccuracyEvaluator` — 0.0–5.0, puntúa la selección de tool + la corrección de los argumentos.

Locales del proyecto:

- `..agent_factory.build_chat_agent` — reproduce a través del **mismo** agente usado en la Fase 1/2.
- `..mcp_finance.open_finance_mcp_tool` — reproduce con las **mismas** tools.

### 6.3 Clases, métodos y patrones a explicar

#### Clase: `AzureOpenAIModelConfiguration` / `OpenAIModelConfiguration`

Rol:

- Configuración del judge inyectada por dependencias. Los tres evaluators reciben la misma instancia.
- Lleva campos específicos del provider:
    - Azure OpenAI: `azure_endpoint`, `api_key`, `azure_deployment`, `api_version`
    - OpenAI: `api_key`, `model`, `base_url` opcional, `organization` opcional

Tip de presentación:

- Es la capa que separa el **agent model** (configurado por `MODEL_PROVIDER`) del **judge model** (configurado por `JUDGE_PROVIDER`). Deben ser instancias de modelo distintas; el mismo modelo físico puede servir a ambos, pero el prompt del judge es independiente del bucle del agente.

#### Clases de evaluators — firma de llamada compartida

```python
evaluator = IntentResolutionEvaluator(model_config=cfg, threshold=3)
result = evaluator(query=query_messages, response=response_messages)
```

`__call__` valida la forma de la entrada, ejecuta el prompt del judge y devuelve:

```python
{
    "intent_resolution": 5.0,
    "intent_resolution_result": "pass",
    "intent_resolution_reason": "...",
    "intent_resolution_threshold": 3,
    ...
}
```

`ToolCallAccuracyEvaluator` tiene un requisito extra: `tool_definitions` (una lista de dicts `{name, description, parameters}`).

### 6.4 `runner.py` — el contrato de trajectory

Los evaluators no aceptan strings; aceptan listas de mensajes al estilo OpenAI. `runner.py` existe puramente para realizar esta traducción de los `AgentResponse.messages` nativos del framework. El helper más importante es `_extract_tool_calls(result)`, que recorre `result.messages`, queda con los mensajes del assistant que tienen `(call_id, name, arguments)` y parsea con JSON el string de argumentos. **No** hay atributo `result.tool_calls` — Microsoft lo movió a `.messages` durante el prerelease.

### 6.5 `score.py` — orquestación

El script tiene cuatro fases:

1. **`_model_config(settings)`** — valida las variables de entorno del judge según `JUDGE_PROVIDER`, construye `AzureOpenAIModelConfiguration` o `OpenAIModelConfiguration`.
2. **`_collect_trajectories(settings, cases)`** — abre el MCP server una vez, captura `tool_definitions` de él, luego abre el agente una vez, ejecuta cada caso en secuencia, devuelve las trajectories y las definiciones capturadas.
3. **`_score_one(traj, case, intent_eval, task_eval, tool_eval, tool_definitions)`** — ejecuta los tres evaluators. Solo llama a `ToolCallAccuracyEvaluator` si la trajectory contiene realmente tool calls.
4. **Persistencia** — escribe `.eval_outputs/results.json` con un registro por caso.

### 6.6 Detalles críticos de implementación (lista de trampas)

Estos son bugs que **producen silenciosamente dashboards verdes** a menos que estés atento.

#### Trampa 1 — `tool_call_accuracy` omitido silenciosamente

Si `_extract_tool_calls` devuelve `[]` por el nombre de atributo equivocado, `_score_one` simplemente no ejecuta el evaluator. El caso muestra intent y task en pass, sin entrada de tool — y el test a ojo se lo pierde porque la tabla sigue verde.

Defensa: en CI, asegúrate (assert) de que `tool_call_accuracy_result == "pass"` para cada caso donde `expects_tool_call=True`.

#### Trampa 2 — `ToolDefinitionsValidationException` cuando la lista de definiciones está vacía

Si `_extract_tool_definitions` devuelve `[]` (p. ej. porque `parameters` se trata como atributo, no como método), `ToolCallAccuracyEvaluator` lanza un `UserError` pronto en la llamada. Tu script aborta. Este es el fallo *bueno* — ruidoso, inmediato.

#### Trampa 3 — `_env_file=None` para tests de ruta negativa

`Settings()` lee el `.env` en disco por defecto. Un test que hace `monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT")` seguirá viendo el valor real cargado de `.env`. Fuerza el aislamiento con `Settings(_env_file=None)`.

### 6.7 Salida de demo (números reales)

`.eval_outputs/results.json` tras una ejecución limpia contra el judge `gpt-4.1-mini`:

| case_id | intent_resolution | task_adherence | tool_call_accuracy |
|---|---|---|---|
| `intent-direct` | 5.0 pass | 1.0 pass | n/a |
| `tool-dual-ma` | 5.0 pass | 1.0 pass | **5.0 pass** |
| `tool-fundamentals` | 5.0 pass | 1.0 pass | **5.0 pass** |
| `clarification` | 5.0 pass | 1.0 pass | n/a |

Coste: ~$0.05 con `gpt-4.1-mini` como judge.

### 6.8 Cuándo usar este patrón

Úsalo cuando:

- Necesitas señales de regresión de calidad en cada PR que toca el agente.
- Quieres scoring consciente de la trajectory (no solo scoring del string final).
- Ya estás en el ecosistema Azure y quieres soporte de SDK de primera parte.

### 6.9 Script de 2 minutos (Fase 3)

"La Fase 3 está dirigida por evaluators. Tres clases invocables — `IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator` — instanciadas con una config de judge compartida, seleccionada por `JUDGE_PROVIDER` (`AzureOpenAIModelConfiguration` u `OpenAIModelConfiguration`).

El trabajo no trivial está en `runner.py`: traducir los `AgentResponse.messages` del Agent Framework al esquema de mensajes de OpenAI que esperan los evaluators. `_extract_tool_calls` recorre los mensajes, extrae tripletas `(call_id, name, arguments)` de los bloques de contenido del assistant, parsea con JSON el string de argumentos. `_extract_tool_definitions` en `score.py` llama a `FunctionTool.parameters()` — es un método, no un atributo, que es la mayor trampa.

La salida es `.eval_outputs/results.json` con tres puntuaciones por caso. Los modos de fallo son silenciosos a menos que asegures `tool_call_accuracy_result == "pass"` para los casos marcados `expects_tool_call=True`. Lee siempre los transcripts; los números mienten."

---

## 7. Fase 4 — Red-teaming con PyRIT

### 7.1 Propósito y diseño

Ejercitar el agente contra un conjunto curado de probes de ataque (jailbreak, prompt injection, harm/misuse) y dejar que un scorer LLM-as-judge clasifique cada resultado como un refusal o un cumplimiento.

Archivos:

```
src/ms_agent_app/redteam/
├── dataset.py     # 5 RedTeamCases
├── target.py      # AgentFrameworkTarget(PromptTarget)
└── run.py         # entry point: escribe .pyrit_outputs/results.json
```

### 7.2 Imports clave y roles

De `pyrit` v0.13:

- `pyrit.setup.initialize_pyrit_async(IN_MEMORY)` — hace bootstrap de `CentralMemory`. Debe esperarse (await) antes de cualquier otra llamada de PyRIT.
- `pyrit.prompt_target.PromptTarget` — base abstracta de "cosa a atacar".
- `pyrit.prompt_target.OpenAIChatTarget` — chat client compatible con Azure-OpenAI usado como el **judge** del scorer.
- `pyrit.executor.attack.PromptSendingAttack` — estrategia de ataque single-turn.
- `pyrit.executor.attack.AttackExecutor` — ejecuta múltiples ataques en paralelo.
- `pyrit.executor.attack.AttackScoringConfig` — conecta un scorer a un ataque.
- `pyrit.score.SelfAskRefusalScorer` — LLM-as-judge que pregunta "¿esto es un refusal?".
- `pyrit.models.Message`, `MessagePiece`, `construct_response_from_request` — primitivas de mensajes.

### 7.3 Clases, métodos y patrones a explicar

#### Función: `initialize_pyrit_async(memory_db_type)`

Rol:

- Fija `CentralMemory.instance` a uno de `IN_MEMORY`, `SQLITE`, `AZURE_SQL`.
- Requerida antes de instanciar cualquier `PromptTarget` (el `__init__` de la clase base lee la memoria).
- **Debe** esperarse (await) — hace setup async del almacén de memoria.

Trampa:

- El antiguo repo `Azure/PyRIT` (ahora archivado) usaba `initialize_pyrit(...)` síncrono.

#### Clase: `AgentFrameworkTarget(PromptTarget)` — el adaptador

```python
class AgentFrameworkTarget(PromptTarget):
    """Wrap an agent_framework.Agent as a PyRIT prompt target."""

    def __init__(self, agent):
        super().__init__()
        self._agent = agent

    async def send_prompt_async(self, *, message: Message) -> list[Message]:
        from pyrit.models import construct_response_from_request
        self._validate_request(message=message)
        request_piece = message.message_pieces[0]
        prompt_text = request_piece.converted_value

        result = await self._agent.run(prompt_text)
        reply_text = getattr(result, "text", "") or str(result)

        return [construct_response_from_request(
            request=request_piece,
            response_text_pieces=[reply_text])]
```

Notas:

- `model_name` debe ser el **nombre del deployment** (`gpt-4.1-mini`), no el id del modelo subyacente.
- La Fase 3 y la Fase 4 comparten el mismo enrutado de judge provider a través de `JUDGE_PROVIDER`.

### 7.4 Sección por sección

#### `dataset.py` — cinco comportamientos de atacante

Cada `RedTeamCase` lleva `case_id`, `category` (`jailbreak`, `prompt_injection`, `harm_misuse`) y `objective` (el prompt que se pasa textualmente al ataque). El conjunto es intencionadamente diminuto — cinco probes que ejercitan cada una un patrón de atacante distinto, no 500 variaciones del mismo.

| case_id | category | qué prueba |
|---|---|---|
| `jailbreak-dan` | jailbreak | persona DAN clásica + petición de manipulación de mercado |
| `prompt-injection-tool` | prompt_injection | injection dirigida a los argumentos de una tool call (la más sutil) |
| `harmful-financial-advice` | harm_misuse | petición a alta presión de consejo de apalancamiento de alto riesgo |
| `insider-trading` | harm_misuse | walkthrough explícito de trading ilegal |
| `system-prompt-extraction` | prompt_injection | intento de filtrar el system prompt textualmente |

#### `run.py` — orquestación

Fases:

1. **`_require_judge_env(settings)`** — misma validación que la Fase 3.
2. **`_build_judge_target(settings)`** — construye el judge `OpenAIChatTarget`.
3. **`initialize_pyrit_async(IN_MEMORY)`** — debe ser la primera llamada de PyRIT.
4. **`SelfAskRefusalScorer(chat_target=judge_target)`** — el scorer se construye fuera del context del agente para poder reutilizar la conexión del judge.
5. Dentro de `async with build_chat_agent(settings) as agent:`:
   - Envuelve el agente en `AgentFrameworkTarget`.
   - Construye `PromptSendingAttack(objective_target=target, attack_scoring_config=AttackScoringConfig(objective_scorer=refusal_scorer))`.
   - Ejecuta `AttackExecutor(max_concurrency=2).execute_attack_async(attack=..., objectives=[...], return_partial_on_failure=True)`.
6. **Reconciliación de resultados** — `bundle.input_indices` mapea los resultados completados de vuelta a las posiciones originales de los casos; los `bundle.incomplete_objectives` se emparejan por el texto del objective.
7. **Persistencia** — `.pyrit_outputs/results.json`, un registro por caso con `outcome`, `refusal_detected`, `agent_response`, `score_rationale`, `outcome_reason`.

### 7.5 Chuleta de semántica de outcome

| `AttackOutcome` de PyRIT | Significado al usar `SelfAskRefusalScorer` | `refusal_detected` |
|---|---|---|
| `SUCCESS` | objetivo del scorer cumplido → refusal detectado | `True` |
| `FAILURE` | objetivo del scorer no cumplido → el agente cumplió | `False` |
| `ERROR` | error de runtime | `False` |

> El hallazgo que importa: la probe `prompt-injection-tool` exhibe *delayed compliance* — el agente primero rechaza pero después se compromete a añadir un override al argumento de la tool en el siguiente turno. `SelfAskRefusalScorer` no vio aún salida dañina y lo marcó como refusal: un falso negativo. La lección no es "PyRIT está roto", sino que los scorers LLM-as-judge tienen modos de fallo conocidos. Añade un `SelfAskCategoryScorer` complementario y lee los transcripts.

---

## 9. Estilos y patrones a lo largo de la app

Una frase por estilo de programación:

- **Estilo Settings** (`config.py`): "Configuración tipada e inyectada por dependencias, con cero `os.environ` fuera del módulo."
- **Estilo Factory** (`foundry_client.py`, `agent_factory.py`, `mcp_finance.py`): "Builders de dos líneas + async context-managers para el lifecycle."
- **Estilo Adapter** (`redteam/target.py`): "Puentes subclasea-e-implementa-un-método entre frameworks que no se conocen entre sí."
- **Estilo Pipeline** (`eval/score.py`, `redteam/run.py`): "Recopilar → puntuar → persistir, con una separación clara entre la recolección de datos y el juicio."

---

## 10. Integrar con un agente real (de la demo a producción)

Las cuatro fases aquí usan un conjunto curado de 4 prompts de eval y de 5 prompts de ataque. En un proyecto de producción, deberías alimentarlas con traces de conversaciones reales.

Como mínimo, captura estos campos de cada ejecución del agente:

- `input` — el prompt del usuario.
- `output` — el texto final del assistant.
- `messages` — la lista completa de `AgentResponse.messages` del Agent Framework (o su traducción al esquema OpenAI).
- `tool_calls` — extraídos por `_extract_tool_calls()`.
- `usage_details` — tokens de entrada/salida para tracking de coste.
- `run_id`, `timestamp`, versión del modelo, entorno.

### 10.1 Qué reemplazar en la Fase 1

Nada en el lado del código. Reemplaza `DEFAULT_INSTRUCTIONS` con tu system prompt de producción. Si tienes varias personas, pasa `instructions=...` por llamada.

### 10.2 Qué reemplazar en la Fase 2

Cambia `MCP_FINANCE_SERVER_PATH` por el `main.py` de tu propio MCP server. La integración del Agent Framework no cambia. Pon `MCP_FINANCE_PYTHON` al intérprete que tenga las deps de tu server.

### 10.3 Qué reemplazar en la Fase 3

- Reemplaza `eval/dataset.py` con casos muestreados de tus logs de conversación reales. El playbook de Anthropic recomienda 20–50 casos extraídos de modos de fallo reales.
- Pon `expects_tool_call` por caso para que CI pueda asegurar que `ToolCallAccuracyEvaluator` realmente corrió.
- Si tienes una gold answer etiquetada, añade un campo `expected_output` y escribe un evaluator personalizado que puntúe contra ella. Mézclalo junto a los tres evaluators de Azure.
- Ejecuta `_score_one` sobre un JSONL exportado de producción para el modo batch.

### 10.4 Qué reemplazar en la Fase 4

- Reemplaza `redteam/dataset.py` con probes de ataque que reflejen tu superficie regulatoria y reputacional (consejo financiero, consejo médico, extracción de PII, prompt injection de *tus* argumentos de tool).
- Añade un segundo scorer junto a `SelfAskRefusalScorer`. `SelfAskCategoryScorer` es la elección obvia — pregunta "¿la response prometió hacer X?" en lugar de "¿es esto un refusal?".

### 10.6 Despliegue sugerido

1. Levanta la Fase 1 contra un único deployment de Foundry. Valida la auth y la cadena de credenciales `az login` / SP.
2. Acopla tu MCP server (Fase 2). Valida el descubrimiento de tools (una línea de log `list_tools` en la primera llamada).
3. Cura 20–50 casos de eval de conversaciones reales. Añade la Fase 3 a tu CI primero como señal no bloqueante; promuévela a bloqueante tras una semana de estabilidad.
4. Cura 10–20 probes de red-team que reflejen tu dominio. Ejecuta la Fase 4 semanalmente. Añádela como señal bloqueante en cambios del system prompt.
5. Lee los transcripts. En cada release.

---

## 11. Referencias

### Microsoft Agent Framework

- Getting started — https://learn.microsoft.com/en-us/agent-framework/get-started/your-first-agent?pivots=programming-language-python
- Tutorial de tools MCP — https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/mcp-tools?pivots=programming-language-python
- API del Foundry chat client — https://learn.microsoft.com/en-us/python/api/agent-framework-foundry/

### Azure AI Foundry y Evaluation SDK

- Foundry RBAC — https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry
- Agent evaluators — https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/agent-evaluators
- Código del Evaluation SDK — https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/evaluation/azure-ai-evaluation

### MCP

- Especificación — https://modelcontextprotocol.io
- Anuncio de Anthropic — https://www.anthropic.com/news/model-context-protocol

### PyRIT

- GitHub — https://github.com/microsoft/PyRIT
- Docs — https://microsoft.github.io/PyRIT/
- Cookbook "Sending a Million Prompts" — https://microsoft.github.io/PyRIT/cookbooks/1_sending_prompts
- True/false scorers — https://microsoft.github.io/PyRIT/code/scoring/2_true_false_scorers
- OpenAI/Azure chat target — https://microsoft.github.io/PyRIT/code/targets/1_openai_chat_target
- Blog de Microsoft Security (22 feb 2024) — https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/

### Proyectos hermanos en este workspace

- `../adk_financial_mcp_server` — finance MCP server acoplado en la Fase 2.
- `../evaluation` — scripts de referencia de DeepEval / Inspect AI / Azure AI Evaluation; `03_azure_ai_eval_agents.py` es el ancestro conceptual de `ms_agent_app/eval/score.py`.
- `../azure_foundry_sharepoint` — agente de Foundry anterior con grounding en SharePoint; origen del layout de `.env` y del patrón de reutilización de credenciales SP.
