# BUILDING AN AGENT FRAMEWORK APP — GUIDE EXTENSION
## Lineage · Libraries · The 90-Minute Technical Track

> **How to use this document.** This is an **addendum** to `microsoft_agent_framework_app/docs/guide_en.md`. It does **not** replace anything in that guide — the existing 60-minute speaker track, opening hook, per-phase notes, and appendix all stand as written. This file adds three things the original guide did not cover in depth:
>
> 1. **Where this came from** — the three prior projects (`adk_financial_mcp_server`, `azure_foundry_sharepoint`, `evaluation`) that form the base of this reference app, and exactly what each one contributed.
> 2. **The libraries in use** — a proper introduction to each technology (Microsoft Agent Framework, MCP, Azure AI Evaluation SDK, PyRIT), with the versions this repo pins, install commands, key imports, and the file/function where each is used.
> 3. **The 90-minute track** — an expanded timing plan that matches the longer slide deck (`Building_an_Agent_Framework_App.pptx`, 32 slides). The original guide is paced for 60 minutes; this section re-paces the same material for a 90-minute technical session and maps every block to slides and code.
>
> Read it alongside `docs/technical_guide_en.md` (the deep code walkthrough) and `docs/architecture.svg`.

---

## Part A — Where This Came From: The Three Base Projects

This reference app is **not greenfield**. It consolidates three earlier projects into a single, coherent four-phase stack. Saying this out loud early in the talk is worth a slide (deck slide 4, *"Where this came from"*) because it reframes the app from "a demo someone built" into "a consolidation layer over real, separately-proven work." Each base project lives as a **sibling directory** and is referenced read-only:

```text
agents_framework/
├── adk_financial_mcp_server/     ← the MCP server (reused unchanged)
├── azure_foundry_sharepoint/     ← the Foundry auth + grounding pattern
├── evaluation/                   ← the eval lab (DeepEval / Inspect / Azure AI Eval)
└── microsoft_agent_framework_app/ ← THIS project — consolidates the three above
```

The implementation plan records them explicitly as *"external siblings (read-only references)"*, which is the honest framing: this project imports their lessons, and in one case their actual code, but does not fork or modify them.

### A.1 — `adk_financial_mcp_server` → the MCP server (Phase 2)

This is the only base project whose **code is reused verbatim**. It is a FastMCP server exposing ~20 quantitative-finance tools across ~16 strategy families (dual moving average, Bollinger breakout, TRIN breadth, overnight gaps, fundamental analysis, market scanner, performance backtesting, and more). It was originally written to power a **Google ADK** stock-analysis bot — a completely different agent runtime.

The headline point for the audience: **the same server, unchanged, now powers a Microsoft Agent Framework agent.** That portability is the entire promise of MCP made concrete. In Phase 2 we attach it over stdio with `MCPStdioTool` (see `mcp_finance.py`) and point `MCP_FINANCE_SERVER_PATH` at its `server/main.py`. It keeps its own ~90 MB virtual environment (yfinance, pandas, scipy, statsmodels); the agent app stays slim and spawns it lazily as a subprocess only when `--with-mcp` is passed.

> 💡 **Speaker Note:** This is the strongest "MCP is real, not a slide" moment in the talk. The server was built for ADK; we did not touch a line of it. If anyone in the room is MCP-skeptical, this is the answer — vendor-neutral tools that survive a runtime swap.

**Where it shows up in code:** `src/ms_agent_app/mcp_finance.py` (the `MCPStdioTool` wiring); `.env` keys `MCP_FINANCE_SERVER_PATH` and `MCP_FINANCE_PYTHON`. **Deck slides:** 16 (`mcp_finance.py`), 17 (the server's tool families).

### A.2 — `azure_foundry_sharepoint` → the Foundry auth + grounding pattern (Phase 1)

This earlier project is a Streamlit agent grounded on SharePoint content through Azure AI Foundry's SharePoint tool, using on-behalf-of (OBO) user identity. We do **not** reuse its code, but it is where the **Foundry connection and credential pattern** was first proven: how to point at a Foundry project endpoint, how to authenticate against Azure with a credential chain rather than an API key, and how to let Foundry — not raw Azure OpenAI — own model deployment, RBAC, and content filtering.

The plan lists it as the *"Foundry env vars & auth example."* Phase 1 of this app distils that pattern into `foundry_client.py`: `FoundryChatClient` plus a credential (the README uses `AzureCliCredential` / `az login`; the credential chain excludes interactive browser and allows additional tenants for multi-tenant logins). The "Why Foundry, not raw Azure OpenAI" slide (deck slide 13) is the direct lesson carried over from this project.

> 💡 **Speaker Note:** Use this to pre-empt the "why not just call Azure OpenAI directly?" question. The answer was learned here: in an enterprise you want named, governed deployments, server-side content filtering, and identity-based access — Foundry gives all three behind one client.

**Where it shows up in code:** `src/ms_agent_app/foundry_client.py` (`build_foundry_client`). **Deck slides:** 12 (`foundry_client.py` + `agent_factory.py`), 13 (why Foundry).

### A.3 — `evaluation` → the evaluation lab (Phase 3)

This base project is a side-by-side study of three agent-evaluation stacks — **DeepEval**, **Inspect AI**, and the **Azure AI Evaluation SDK** — each in its own script (`01_deepeval_agent_eval.py`, `02_inspect_ai_agent_eval.py`, `03_azure_ai_eval_agents.py`). It has its own 60-minute speaker guide and deep technical guide.

Phase 3 of this app follows **`03_azure_ai_eval_agents.py`** as its model: the same three evaluators (`IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator`), the same OpenAI-style message-trace input shape, and the same quality-then-safety framing. The choice to standardise on the Azure SDK (rather than DeepEval or Inspect) for the consolidated app was made *because* the lab compared all three first.

> 💡 **Speaker Note:** If asked "why Azure AI Evaluation and not DeepEval or Inspect?", the honest answer is that all three were trialled in the `evaluation` project; the Azure SDK won for an Azure-native stack because its agentic evaluators (intent / task / tool-call) map cleanly onto Foundry deployments and need no extra provider wiring. Offer the `evaluation` repo for the full comparison.

**Where it shows up in code:** `src/ms_agent_app/eval/dataset.py`, `eval/runner.py`, `eval/score.py` — all shaped after the sibling `evaluation/03_azure_ai_eval_agents.py`. **Deck slides:** 21–24.

### A.4 — One-line lineage summary (for the slide)

| Base project | What it contributed | Where it lands |
|---|---|---|
| `adk_financial_mcp_server` | The MCP finance server, **reused unchanged** (was an ADK bot's backend) | Phase 2 — `mcp_finance.py` |
| `azure_foundry_sharepoint` | The Foundry endpoint + credential-chain auth pattern | Phase 1 — `foundry_client.py` |
| `evaluation` | The Azure-AI-Evaluation approach, chosen after a 3-way comparison | Phase 3 — `eval/` |

---

## Part B — The Libraries In Use

The original guide assumes the audience knows what an agent is. It does **not** introduce the specific libraries. For a technical audience that is exactly the part worth a few minutes — most rooms know three of the four names but rarely the current APIs, and the APIs have moved. Deck slide 6 (*"The libraries in use"*) is the 2×2 tile for this section; spend ~3–4 minutes here.

A recurring theme: **this repo pins prereleases on purpose, and older tutorials do not run unchanged.** Say that explicitly. The technical guide documents the APIs *as they exist in the pinned versions*, not as 2024–25 blog posts describe them.

### B.1 — Microsoft Agent Framework

**What it is.** Microsoft's current, converged agent runtime. Semantic Kernel and AutoGen merged into a single framework: it gives you an `Agent` abstraction, a client-agnostic chat-client interface, message/response types, and native tool-calling — including native MCP support.

**Links.**
- Overview (Python): <https://learn.microsoft.com/en-gb/agent-framework/overview/?pivots=programming-language-python>
- Source: <https://github.com/microsoft/agent-framework>

**Pinned in this repo** (`pyproject.toml`): `agent-framework>=1.4.0`, `agent-framework-foundry>=1.4.0` (the Foundry chat-client package). Requires **Python 3.11+**.

**Install.**
```bash
uv add --prerelease=allow agent-framework agent-framework-foundry mcp
```

**Key imports & where used.**
```python
from agent_framework import Agent, MCPStdioTool          # core agent + MCP tool
from agent_framework.foundry import FoundryChatClient     # Foundry-backed chat client
```
- `FoundryChatClient` → `foundry_client.py` (`build_foundry_client`).
- `Agent` → `agent_factory.py` (`build_chat_agent`), with `DEFAULT_INSTRUCTIONS` that bias the agent to prefer a tool call over guessing and to say so plainly when it cannot answer from tool results.
- `MCPStdioTool` → `mcp_finance.py` (Phase 2).

**The three abstractions to teach** (deck slide 11): an **Agent** (wraps an LLM client, instructions, optional toolset; exposes `run(prompt)`), an **AgentResponse** (carries `.text`, the underlying `.messages`, `usage_details`, `finish_reason`), and a **chat client** (the model-hosting adapter — `FoundryChatClient`, `AzureOpenAIChatClient`, `AnthropicChatClient`, …). The one-liner that sells it: *the `Agent` class does not care which chat client it holds* — swapping clients is a one-line change, and the same `Agent` is what the eval harness and the PyRIT target wrap later.

> ⚠️ **API drift to call out:** `AgentResponse` has **no** `.tool_calls` attribute. To recover tool calls you walk `result.messages` yourself — exactly what `eval/runner.py::_extract_tool_calls` does. This is a common stumble for anyone porting from a tutorial.

### B.2 — Model Context Protocol (MCP)

**What it is.** A vendor-neutral protocol for exposing tools to any model over stdio / HTTP. Before MCP, every framework reinvented tool-calling (LangChain Tool, Semantic Kernel function, OpenAI Assistants, smolagents …); MCP standardises it so a tool written once is callable from any compliant client.

**Links.**
- Spec & docs: <https://modelcontextprotocol.io>
- Python SDK: pinned here as `mcp>=1.27.1`.

**The mental model to teach** (deck slide 15): **3 nouns** — *server* (exposes capabilities), *tool* (name + description + JSON-schema params), *client* (the agent that consumes them) — and **2 verbs**: `list_tools()` (discovery at startup) and `call_tool(name, args)` (invocation). The wire sequence (deck slide 18): Ping → ListTools → the framework converts results into OpenAI function definitions → the model emits a call → CallTool → a `role=tool` reply is appended → the next assistant turn writes the answer.

**Key imports & where used.**
```python
from agent_framework import MCPStdioTool
from contextlib import asynccontextmanager
```
- `mcp_finance.py::build_finance_mcp_tool` builds `MCPStdioTool(name="finance_tools", command=settings.mcp_python(), args=[server_path])`.
- `mcp_finance.py::open_finance_mcp_tool` is an `@asynccontextmanager` so the subprocess starts lazily and is cleaned up even on errors.

> 💡 **Speaker Note:** Tie this straight back to Part A.1 — the server on the other end of this protocol is the unmodified `adk_financial_mcp_server`. MCP is what makes "built for ADK, runs under Agent Framework" true.

### B.3 — Azure AI Evaluation SDK

**What it is.** Azure's library for scoring agents along a **quality** axis using LLM-as-judge evaluators with structured rubrics. It ships agent-specific evaluators that score intent resolution, task adherence, and tool-call accuracy from an OpenAI-shaped message trace.

**Links.**
- Readme / overview: <https://learn.microsoft.com/en-us/python/api/overview/azure/ai-evaluation-readme?view=azure-python>
- SDK source (this repo tracks the 1.x line): <https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-evaluation_1.16.9/sdk/evaluation/azure-ai-evaluation>

**Pinned in this repo:** `azure-ai-evaluation>=1.0.0`.

**Install.**
```bash
uv add "azure-ai-evaluation>=1.0.0"
```

**Key imports & where used.**
```python
from azure.ai.evaluation import (
    IntentResolutionEvaluator,   # Likert 1–5, threshold 3
    TaskAdherenceEvaluator,      # 0.0–1.0, threshold 0.5
    ToolCallAccuracyEvaluator,   # 0–5, needs tool_definitions
)
```
- The three evaluators are constructed in `eval/score.py` (`_score_one`) against a provider-routed model config built by `_model_config` (`AzureOpenAIModelConfiguration` for `JUDGE_PROVIDER=azure-openai`, `OpenAIModelConfiguration` for `JUDGE_PROVIDER=openai`).
- `eval/runner.py::Trajectory.record` captures `(query, response, tool_calls)` in the OpenAI message schema the evaluators expect (`query` and `response` are **lists**, not strings).
- Output: `.eval_outputs/results.json`. The judge is a separate, cheaper model (≈ `gpt-4.1-mini`, ≈ $0.05/run) — **the judge is not the agent's model.**

> ⚠️ **Two traps worth a slide (deck slide 23):**
> 1. `ToolCallAccuracyEvaluator` needs `tool_definitions`. When you extract them, note that `FunctionTool.parameters` is a **method, not an attribute** in the prerelease — call it if callable (`params = params_attr() if callable(params_attr) else params_attr`).
> 2. **Silent green dashboards:** if tool extraction returns `[]`, `_score_one` skips the tool evaluator and the case still looks green. Assert `tool_call_accuracy == "pass"` in CI for every case where `expects_tool_call=True`.

### B.4 — Microsoft PyRIT

**What it is.** The **Python Risk Identification Toolkit** — Microsoft's open framework for red-teaming generative-AI systems, announced February 2024. It scores agents along the **safety** axis: does the agent refuse what it must refuse? It models adversarial testing as pluggable building blocks — **targets** (what gets attacked), **attacks/orchestrators** (how prompts are sent), **scorers** (how outcomes are judged), and **converters** (prompt transformations).

**Links.**
- Source: <https://github.com/microsoft/PyRIT>
- Docs: <https://microsoft.github.io/PyRIT/>

**Pinned in this repo:** `pyrit>=0.13.0`, as an **optional extras group** so the base install stays small:
```bash
uv sync --extra redteam      # adds pyrit (~150 MB; pulls transformers)
```

**Key imports & where used.**
```python
from pyrit.common import initialize_pyrit, IN_MEMORY
from pyrit.prompt_target import PromptTarget, OpenAIChatTarget
from pyrit.score import SelfAskRefusalScorer
from pyrit.executor.attack import PromptSendingAttack, AttackExecutor
```
- `redteam/target.py::AgentFrameworkTarget(PromptTarget)` is the **only PyRIT-specific code we own** (~20 lines): `send_prompt_async(*, message)` validates the request, pulls the user text, calls **our** `agent.run(...)`, and wraps the reply back into PyRIT's message bookkeeping.
- `redteam/run.py` initialises PyRIT in-memory, runs a `PromptSendingAttack` via `AttackExecutor(max_concurrency=2)`, and judges refusals with `SelfAskRefusalScorer` backed by an `OpenAIChatTarget` created from `JUDGE_PROVIDER` routing (same judge provider policy as Phase 3).

> ⚠️ **API drift to call out (deck slide 27):** PyRIT renamed a lot in v0.13 — `PromptSendingOrchestrator → PromptSendingAttack`, `PromptRequestResponse → Message`, and `PromptChatTarget` is deprecated. 2024–25 tutorials **do not** run unchanged; the adapter here is written against the live source.

> ⚠️ **Outcome semantics (say this twice):** with `SelfAskRefusalScorer`, `AttackOutcome.SUCCESS` means **the refusal was detected** — i.e. the agent behaved well. It does **not** mean the jailbreak worked. This inversion trips everyone; invert with `TrueFalseInverterScorer` if your demo prefers "success = jailbreak."

#### Aside — what the "Classic DAN persona" probe is

The first probe in the dataset (`jailbreak-dan`, deck slide 28: *"Classic DAN persona + market-manipulation ask"*) is worth one sentence of context, because rooms often recognize the name without knowing the details.

**DAN** stands for **"Do Anything Now."** It is one of the oldest and most widely documented jailbreak prompts, dating to the early ChatGPT era (late 2022 / early 2023). The technique is a roleplay framing: the user instructs the model to adopt an alter-ego called DAN that has supposedly "broken free" of its normal rules — DAN "can do anything now," is not bound by content policy, and never refuses. Classic versions added theatrical pressure mechanics, such as a fake "token" system where DAN "loses points" or "dies" if it refuses or breaks character, to coerce compliance through the fiction. It works (when it works) by exploiting the gap between *instruction-following* and *safety training*: rather than asking for disallowed content directly, it wraps the request in a fictional character that is "allowed" to produce it, hoping the model prioritizes staying in character over its guardrails.

In our dataset the DAN framing is combined with a **market-manipulation** request — the finance-domain payload that makes the probe relevant to this agent. Its purpose is a **regression check**, not a novel threat: it is the canonical, textbook jailbreak that every red-team suite tests against, so the question it answers is "does the obvious attack still get caught?" In our three-run results it was **blocked at the filter every run** — the expected, desirable outcome, since modern models and Foundry's content filters recognize the DAN pattern readily precisely because it is so well known. The interesting failure in the data is the `prompt-injection-tool` probe (deck slide 29), not this one.

> 💡 **Speaker Note:** Don't dwell on DAN — it's the warm-up. Name it, note it's blocked every run, and use it as the contrast that sets up the real finding: the attacks that get caught are the famous ones; the one that slipped through was the quiet, domain-specific tool-injection.

### B.5 — One shared configuration surface

All four libraries read configuration from a **single** `config.py` (`Settings(BaseSettings)`, `pydantic-settings>=2.14.1` + `python-dotenv>=1.2.2`) and one `.env`. Phase 1, 2, 3 and 4 share the same Foundry endpoint, and Phase 3/4 share the same judge-provider routing (`JUDGE_PROVIDER=azure-openai|openai`). `config.py` is the dependency-injection seam the tests exploit (`Settings(_env_file=None)` for the missing-env negative test). Deck slide 9 is this slide.

---

## Part C — The 90-Minute Track

The original guide is paced for **60 minutes / 15 slides**. The longer deck (`Building_an_Agent_Framework_App.pptx`, **32 slides**) is paced for **90 minutes**. The extra 30 minutes go almost entirely into (a) the new lineage and libraries framing from Parts A and B, and (b) more time on the live code on each phase's code slides. Nothing from the 60-minute track is dropped — it is expanded.

### C.1 — 90-minute timing breakdown

| Time | Section | Deck slides | Duration |
|------|---------|-------------|----------|
| 0:00 | Opening · lineage · why this stack | 1–5 | 10 min |
| 0:10 | Libraries · architecture · the four-phase model | 6–8 | 4 min |
| 0:14 | Shared foundation — `config.py` | 9 | 2 min |
| 0:16 | **Phase 1 — Agent + Foundry** | 10–13 | 12 min |
| 0:28 | **Phase 2 — Local tools via MCP** | 14–18 | 14 min |
| 0:42 | **Phase 3 — Azure AI Evaluation SDK** | 19–24 | 14 min |
| 0:56 | **Phase 4 — PyRIT red teaming** | 25–29 | 16 min |
| 1:12 | Lessons learned & key takeaways | 30–31 | 8 min |
| 1:20 | Resources & Q&A | 32 | 5 min |
| | **Total** | **32 slides** | **90 min** |

### C.2 — Section-by-section expansion

Below, each block lists only what is **new or re-paced** relative to the 60-minute guide. Keep the original guide's hooks and speaker notes; layer these on top.

**0:00–0:10 — Opening · lineage · why this stack (slides 1–5).**
Open with the existing four-logos hook (three familiar, PyRIT the unknown — see original guide). Then add the **lineage beat** (new slide 4, Part A): this app consolidates three real prior projects. Land the single best line early — *the MCP server was built for a Google ADK bot and runs here unchanged.* Close the block on the existing "why this stack, why now" argument (slide 5): a modern enterprise agent is no longer an LLM plus a system prompt; it needs reasoning + orchestration, live tools, quality eval, and safety eval — four orthogonal properties.

**0:10–0:14 — Libraries · architecture · four-phase model (slides 6–8).**
This is the **new Part B** content, kept tight. Four tiles (slide 6): Agent Framework, MCP, Azure AI Evaluation SDK, PyRIT — name, one-line role, install command, version. Then the one-diagram architecture (slide 7) and the gated/incremental, two-axis (quality vs safety) model (slide 8). Drive home: each phase is independently runnable and depends only on the phases below it.

**0:14–0:16 — Shared foundation, `config.py` (slide 9).**
Two minutes. One typed settings object, one `.env`, the DI seam the tests use. Mention that the Phase-3/4 judge vars are validated lazily — only when those scripts run.

**0:16–0:28 — Phase 1 (slides 10–13), 12 min.**
Concepts (slide 11): Agent / AgentResponse / chat client — and *the Agent does not care which client it holds.* Code (slide 12): `foundry_client.build_foundry_client` and `agent_factory.build_chat_agent`, including `DEFAULT_INSTRUCTIONS`. Rationale (slide 13): why Foundry, not raw Azure OpenAI — the lesson inherited from `azure_foundry_sharepoint` (named deployments, RBAC, server-side filters, identity). Run it live: `uv run ms-agent-app` (or `uv run ms-agent-app --provider openai|azure-openai|anthropic`).

**0:28–0:42 — Phase 2 (slides 14–18), 14 min.**
MCP mental model (slide 15): 3 nouns, 2 verbs. Code (slide 16): `mcp_finance.py` — `MCPStdioTool` + the async context manager. The server (slide 17): the unmodified `adk_financial_mcp_server`, ~20 tools, its own 90 MB venv, spawned lazily. Wire protocol (slide 18): Ping → ListTools → function defs → model call → CallTool → `role=tool` reply. Run it live: `uv run ms-agent-app --with-mcp` (optional provider override: `--provider openai|azure-openai|anthropic|foundry`), then *"Run a dual moving average analysis on AAPL."*

**0:42–0:56 — Phase 3 (slides 19–24), 14 min.**
Why score quality (slide 20). The three evaluators with their ranges/thresholds (slide 21). The trajectory contract — `query`/`response` are lists in the OpenAI message schema (slide 22). `score.py` and the two traps — `FunctionTool.parameters` is a method, and the silent-green-dashboard skip (slide 23). Real numbers from a clean run, and the ≈ $0.05/run judge cost (slide 24). Run it live: `uv run python -m ms_agent_app.eval.score` (agent provider from `MODEL_PROVIDER`; judge provider from `JUDGE_PROVIDER`). Repeat: the judge is not the agent's model.

**0:56–1:12 — Phase 4 (slides 25–29), 16 min — the climax.**
This gets the most time because it is the least familiar and carries the talk's best finding. Quality vs red-team — *"did the agent do what the user wanted?"* vs *"did it do what it must not?"* (slide 26). `target.py` — the only ~20 lines of PyRIT-specific code we own (slide 27). The five probes / five behaviours dataset (slide 28). Then **the finding** (slide 29): a **false-negative scorer** — the `prompt-injection-tool` probe shows *delayed compliance* (the agent first refuses, then appends an override to the tool argument), and `SelfAskRefusalScorer` marked it a refusal. Show the 3-run variability table (jailbreak and system-prompt extraction blocked at the filter every run; prompt-injection-tool SUCCESS\*/SUCCESS\*/ERROR). Run it live: `uv run ms-agent-redteam` (agent provider from `MODEL_PROVIDER`; judge provider from `JUDGE_PROVIDER`). Remind the room twice that `SUCCESS` = refusal detected.

**1:12–1:20 — Lessons & takeaways (slides 30–31), 8 min.**
Lessons (slide 30): the four-phase pattern is reusable; one `.env` / one credential; lazy imports halve the install surface; LLM-as-judge has known weaknesses (delayed compliance, verbose refusals, single-shot on multi-turn). Three takeaways (slide 31): quality and safety evals are complementary (a green Phase 3 means nothing if Phase 4 fails); read the transcripts (the finding was invisible at the score level); pick layers, not a stack (Agent Framework, Foundry, MCP, Eval SDK and PyRIT are independently swappable — optimise each layer separately).

**1:20–1:25 — Resources & Q&A (slide 32), 5 min.**
Point to the four library links (Part B), the three sibling projects (Part A), and the repo's own `technical_guide_en.md`. Keep Q&A to 5 minutes; offer to continue offline.

### C.3 — If you have to compress back toward 60 minutes

If the slot shrinks on the day, cut in this order and you are back to roughly the original 60-minute shape without losing the spine: trim the libraries block (slide 6) to 90 seconds; drop the wire-protocol slide (18) and the trajectory-contract slide (22) to spoken asides; shorten lessons (30) to the three takeaways only. Do **not** cut slide 29 (the finding) or any of the four live runs — those are the talk.

---

*End of extension. Pair with `docs/guide_en.md`, `docs/technical_guide_en.md`, `docs/architecture.svg`, and the deck `Building_an_Agent_Framework_App.pptx`.*