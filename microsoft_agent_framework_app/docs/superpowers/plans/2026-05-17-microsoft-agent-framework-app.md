# Microsoft Agent Framework App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python chat agent on the Microsoft Agent Framework that talks to Azure AI Foundry, calls a local financial MCP server, and is scored with the Azure AI Evaluation SDK.

**Architecture:** Single-process CLI app in `src/ms_agent_app/`. `FoundryChatClient` (via `agent-framework-foundry`) is wrapped in an `Agent`. A second mode attaches the existing `adk_financial_mcp_server` over stdio with `MCPStdioTool`. A separate `eval/` module replays curated prompts, captures OpenAI-shape message trajectories, and scores them with `IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, and `ToolCallAccuracyEvaluator`.

**Tech Stack:** Python 3.11+, `uv`, `agent-framework` (prerelease), `agent-framework-foundry` (prerelease), `mcp` (prerelease), `azure-identity`, `azure-ai-evaluation`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `ruff`.

**Working directory:** `/mnt/d/repos2/agents_framework/microsoft_agent_framework_app/`

**External siblings (read-only references):**
- `../azure_foundry_sharepoint/` — Foundry env vars & auth example
- `../adk_financial_mcp_server/server/main.py` — the stdio MCP server we attach in Phase 2
- `../evaluation/03_azure_ai_eval_agents.py` — Azure AI Evaluation SDK reference

---

## Phase 0 — Project Bootstrap with `uv`

### Task 0.1: Initialize `uv` package layout

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/ms_agent_app/__init__.py`

- [ ] **Step 1: Initialize the package skeleton**

Run from `/mnt/d/repos2/agents_framework/microsoft_agent_framework_app/`:

```bash
uv init --package --name ms-agent-app --python 3.11
```

Expected: creates `pyproject.toml`, `.python-version`, and `src/ms_agent_app/__init__.py`.

- [ ] **Step 2: Verify the layout**

Run:

```bash
ls -la && cat pyproject.toml
```

Expected: `pyproject.toml` contains `[project] name = "ms-agent-app"` and `requires-python = ">=3.11"`.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml .python-version src/ms_agent_app/__init__.py
git commit -m "chore: scaffold ms-agent-app with uv"
```

> If the parent dir is not a git repo, `git init` first and add a `.gitignore` (see Task 0.4) before committing.

### Task 0.2: Add runtime dependencies

**Files:**
- Modify: `pyproject.toml` (via `uv add`)
- Create: `uv.lock`

- [ ] **Step 1: Add Agent Framework + Foundry + MCP (prerelease)**

```bash
uv add --prerelease=allow agent-framework agent-framework-foundry mcp
```

Expected: resolves all three; lock file appears. If `agent-framework[all]` is preferred, use that instead — but pin to the explicit packages so we don't pull unneeded subpackages.

- [ ] **Step 2: Add Azure auth, settings, dotenv**

```bash
uv add azure-identity python-dotenv pydantic-settings
```

- [ ] **Step 3: Add Azure AI Evaluation SDK**

```bash
uv add "azure-ai-evaluation>=1.0.0"
```

- [ ] **Step 4: Verify imports resolve**

```bash
uv run python -c "from agent_framework import Agent, MCPStdioTool; from agent_framework.foundry import FoundryChatClient; from azure.ai.evaluation import IntentResolutionEvaluator; print('ok')"
```

Expected: prints `ok`. If `MCPStdioTool` import fails, re-run `uv add --prerelease=allow mcp`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add agent-framework, foundry, mcp, azure-ai-evaluation"
```

### Task 0.3: Add dev dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dev group**

```bash
uv add --dev pytest pytest-asyncio ruff
```

- [ ] **Step 2: Configure ruff and pytest in pyproject.toml**

Append to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "RUF"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Verify**

```bash
uv run ruff --version && uv run pytest --version
```

Expected: both print versions without error.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add dev tooling (pytest, ruff)"
```

### Task 0.4: `.env.example`, `.gitignore`, `README.md`

**Files:**
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Write `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
uv.lock.bak
.eval_outputs/
```

- [ ] **Step 2: Write `.env.example`**

```dotenv
# Azure AI Foundry (used by Phase 1 + 2)
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4.1
# Optional - only if you don't have a default tenant on `az login`
# AZURE_TENANT_ID=

# Local MCP finance server (Phase 2)
MCP_FINANCE_SERVER_PATH=../adk_financial_mcp_server/server/main.py
# Path to the Python interpreter that has the finance server's deps installed.
# Easiest: point at the .venv created inside adk_financial_mcp_server.
MCP_FINANCE_PYTHON=../adk_financial_mcp_server/server/.venv/bin/python

# Azure AI Evaluation SDK judge model (Phase 3)
AZURE_DEPLOYMENT_NAME=gpt-4o
AZURE_API_KEY=
AZURE_ENDPOINT=https://<your-aoai-resource>.cognitiveservices.azure.com/
AZURE_API_VERSION=2024-12-01-preview
```

- [ ] **Step 3: Write minimal `README.md`**

```markdown
# ms-agent-app

Microsoft Agent Framework demo: Foundry-backed chat agent + local financial MCP tools + Azure AI Evaluation SDK scoring.

## Setup

```bash
uv sync
cp .env.example .env  # fill in values
az login              # for FoundryChatClient
```

## Run

```bash
uv run ms-agent-app                      # Phase 1: chat only
uv run ms-agent-app --with-mcp           # Phase 2: chat + finance MCP
uv run python -m ms_agent_app.eval.score # Phase 3: evaluation
```
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example README.md
git commit -m "chore: add env example, gitignore, README"
```

---

## Phase 1 — Local Agent Connected to Azure AI Foundry

### Task 1.1: Typed settings loader

**Files:**
- Create: `src/ms_agent_app/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest
from ms_agent_app.config import Settings


def test_settings_requires_foundry_endpoint(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", raising=False)
    with pytest.raises(ValueError):
        Settings()


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    s = Settings()
    assert s.foundry_project_endpoint == "https://x/api/projects/p"
    assert s.foundry_model_deployment_name == "gpt-4.1"


def test_mcp_server_path_resolves_relative(monkeypatch, tmp_path):
    server = tmp_path / "main.py"
    server.write_text("# stub")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.setenv("MCP_FINANCE_SERVER_PATH", str(server))
    s = Settings()
    assert s.mcp_finance_server_path == server
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```

Expected: ImportError / ModuleNotFoundError on `ms_agent_app.config`.

- [ ] **Step 3: Implement `config.py`**

```python
# src/ms_agent_app/config.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    foundry_project_endpoint: str = Field(..., alias="FOUNDRY_PROJECT_ENDPOINT")
    foundry_model_deployment_name: str = Field(..., alias="FOUNDRY_MODEL_DEPLOYMENT_NAME")
    azure_tenant_id: Optional[str] = Field(None, alias="AZURE_TENANT_ID")

    mcp_finance_server_path: Optional[Path] = Field(None, alias="MCP_FINANCE_SERVER_PATH")
    mcp_finance_python: Optional[str] = Field(None, alias="MCP_FINANCE_PYTHON")

    azure_deployment_name: Optional[str] = Field(None, alias="AZURE_DEPLOYMENT_NAME")
    azure_api_key: Optional[str] = Field(None, alias="AZURE_API_KEY")
    azure_endpoint: Optional[str] = Field(None, alias="AZURE_ENDPOINT")
    azure_api_version: Optional[str] = Field("2024-12-01-preview", alias="AZURE_API_VERSION")

    @field_validator("mcp_finance_server_path", mode="before")
    @classmethod
    def _resolve_server_path(cls, v):
        if not v:
            return None
        return Path(v).expanduser().resolve()

    def mcp_python(self) -> str:
        """Interpreter for the MCP server subprocess; falls back to current sys.executable."""
        return self.mcp_finance_python or sys.executable
```

> Pydantic raises `ValidationError` (a subclass of `ValueError`) when required env vars are missing, so the first test passes as-is.

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add src/ms_agent_app/config.py tests/test_config.py
git commit -m "feat(config): typed Settings with .env loading"
```

### Task 1.2: Foundry client + agent factory

**Files:**
- Create: `src/ms_agent_app/foundry_client.py`
- Create: `src/ms_agent_app/agent_factory.py`
- Test: `tests/test_agent_factory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_factory.py
from unittest.mock import MagicMock, patch

from ms_agent_app.agent_factory import build_chat_agent
from ms_agent_app.config import Settings


def _stub_settings(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    return Settings()


def test_build_chat_agent_uses_foundry_client(monkeypatch):
    settings = _stub_settings(monkeypatch)
    with patch("ms_agent_app.foundry_client.FoundryChatClient") as foundry_mock, \
         patch("ms_agent_app.foundry_client.AzureCliCredential") as cred_mock, \
         patch("ms_agent_app.agent_factory.Agent") as agent_mock:
        foundry_instance = MagicMock()
        foundry_mock.return_value = foundry_instance
        cred_mock.return_value = MagicMock()
        agent_mock.return_value = MagicMock()

        agent = build_chat_agent(settings, name="TestAgent", instructions="hi")

        foundry_mock.assert_called_once()
        _, foundry_kwargs = foundry_mock.call_args
        assert foundry_kwargs["project_endpoint"] == "https://x/api/projects/p"
        assert foundry_kwargs["model"] == "gpt-4.1"
        agent_mock.assert_called_once()
        _, agent_kwargs = agent_mock.call_args
        assert agent_kwargs["name"] == "TestAgent"
        assert agent_kwargs["instructions"] == "hi"
        assert agent_kwargs["client"] is foundry_instance
        assert agent is agent_mock.return_value
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_agent_factory.py -v
```

Expected: ModuleNotFoundError on `ms_agent_app.agent_factory`.

- [ ] **Step 3: Implement `foundry_client.py`**

```python
# src/ms_agent_app/foundry_client.py
from __future__ import annotations

from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from .config import Settings


def build_foundry_client(settings: Settings) -> FoundryChatClient:
    """Create a FoundryChatClient using `az login` credentials.

    Authentication: relies on `az login` being completed in the shell.
    """
    credential = AzureCliCredential(tenant_id=settings.azure_tenant_id) \
        if settings.azure_tenant_id else AzureCliCredential()

    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model_deployment_name,
        credential=credential,
    )
```

- [ ] **Step 4: Implement `agent_factory.py`**

```python
# src/ms_agent_app/agent_factory.py
from __future__ import annotations

from typing import Iterable, Optional

from agent_framework import Agent

from .config import Settings
from .foundry_client import build_foundry_client


DEFAULT_INSTRUCTIONS = (
    "You are a careful, concise assistant. "
    "If the user's question is about markets, equities, or trading strategies, "
    "and tools are available, prefer calling a tool over guessing. "
    "If you cannot answer from tool results, say so plainly."
)


def build_chat_agent(
    settings: Settings,
    *,
    name: str = "FoundryAgent",
    instructions: str = DEFAULT_INSTRUCTIONS,
    tools: Optional[Iterable[object]] = None,
) -> Agent:
    """Build an Agent bound to Azure AI Foundry. Tools are optional and may be passed
    per-call to `agent.run(...)` instead."""
    client = build_foundry_client(settings)
    kwargs: dict = {"client": client, "name": name, "instructions": instructions}
    if tools is not None:
        kwargs["tools"] = list(tools)
    return Agent(**kwargs)
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_agent_factory.py -v
```

Expected: passes.

- [ ] **Step 6: Commit**

```bash
git add src/ms_agent_app/foundry_client.py src/ms_agent_app/agent_factory.py tests/test_agent_factory.py
git commit -m "feat(agent): foundry client + agent factory"
```

### Task 1.3: CLI entrypoint (chat-only)

**Files:**
- Create: `src/ms_agent_app/cli.py`
- Modify: `pyproject.toml` (add `[project.scripts]`)

- [ ] **Step 1: Implement `cli.py`**

```python
# src/ms_agent_app/cli.py
from __future__ import annotations

import argparse
import asyncio
import sys

from .agent_factory import build_chat_agent
from .config import Settings


async def _chat_loop(use_mcp: bool) -> None:
    settings = Settings()

    if use_mcp:
        # Imported lazily so Phase 1 doesn't require MCP wiring to import.
        from .mcp_finance import open_finance_mcp_tool

        async with open_finance_mcp_tool(settings) as mcp_server:
            async with build_chat_agent(settings) as agent:
                await _repl(agent, tools=mcp_server)
    else:
        async with build_chat_agent(settings) as agent:
            await _repl(agent, tools=None)


async def _repl(agent, tools) -> None:
    print("ms-agent-app — type 'exit' to quit.")
    while True:
        try:
            user = input("you> ").strip()
        except EOFError:
            print()
            return
        if not user:
            continue
        if user.lower() in {"exit", "quit", ":q"}:
            return
        kwargs = {"tools": tools} if tools is not None else {}
        result = await agent.run(user, **kwargs)
        text = getattr(result, "text", None) or str(result)
        print(f"agent> {text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ms-agent-app")
    parser.add_argument("--with-mcp", action="store_true", help="Attach local finance MCP server.")
    args = parser.parse_args(argv)
    try:
        asyncio.run(_chat_loop(args.with_mcp))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Register the script entrypoint**

Append to `pyproject.toml`:

```toml
[project.scripts]
ms-agent-app = "ms_agent_app.cli:main"
```

- [ ] **Step 3: Smoke-run without MCP**

Requires a real `.env` and `az login`:

```bash
uv sync
uv run ms-agent-app
```

Expected: prompt opens, you type "Say hi in one sentence.", agent replies via Foundry. Type `exit`.

If you don't yet have Foundry creds, skip the smoke-run and just verify the CLI parses:

```bash
uv run python -c "from ms_agent_app.cli import main; main(['--help'])"
```

Expected: argparse help text including `--with-mcp`.

- [ ] **Step 4: Commit**

```bash
git add src/ms_agent_app/cli.py pyproject.toml
git commit -m "feat(cli): chat REPL backed by Foundry"
```

---

## Phase 2 — Attach Local Financial MCP Server

### Task 2.1: Prepare the MCP server runtime

The MCP server lives at `../adk_financial_mcp_server/server/main.py` and has its own deps (numpy, pandas, yfinance, etc.). Two options — pick one and proceed:

- **Option A (recommended):** create a dedicated venv inside that folder so our app stays slim.
- **Option B:** install its deps into our project's venv (not recommended; couples concerns).

- [ ] **Step 1 (Option A): Sync the finance server's own environment**

```bash
cd ../adk_financial_mcp_server/server
uv sync
cd -
```

Expected: a `.venv/` is created at `../adk_financial_mcp_server/server/.venv/` with `fastmcp`, `yfinance`, etc.

- [ ] **Step 2: Verify the server starts (stdio handshake)**

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  | ../adk_financial_mcp_server/server/.venv/bin/python ../adk_financial_mcp_server/server/main.py 2>/dev/null | head -1
```

Expected: a single JSON response containing `"protocolVersion"` and `serverInfo.name == "finance tools"`. If you don't see anything, run the server interactively to see import errors:

```bash
../adk_financial_mcp_server/server/.venv/bin/python ../adk_financial_mcp_server/server/main.py
```

(Use `Ctrl-C` to kill — it's waiting for stdin.)

- [ ] **Step 3: Update `.env`**

Set:

```
MCP_FINANCE_SERVER_PATH=../adk_financial_mcp_server/server/main.py
MCP_FINANCE_PYTHON=../adk_financial_mcp_server/server/.venv/bin/python
```

> No commit yet — just config. `.env` is gitignored.

### Task 2.2: `mcp_finance.py` — build `MCPStdioTool`

**Files:**
- Create: `src/ms_agent_app/mcp_finance.py`
- Test: `tests/test_mcp_finance.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mcp_finance.py
from pathlib import Path
from unittest.mock import patch

from ms_agent_app.config import Settings
from ms_agent_app.mcp_finance import build_finance_mcp_tool


def _settings(monkeypatch, tmp_path: Path) -> Settings:
    server = tmp_path / "main.py"
    server.write_text("# stub server")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.setenv("MCP_FINANCE_SERVER_PATH", str(server))
    monkeypatch.setenv("MCP_FINANCE_PYTHON", "/usr/bin/python3")
    return Settings()


def test_build_finance_mcp_tool_uses_configured_command(monkeypatch, tmp_path):
    settings = _settings(monkeypatch, tmp_path)
    with patch("ms_agent_app.mcp_finance.MCPStdioTool") as ToolMock:
        tool = build_finance_mcp_tool(settings)
        ToolMock.assert_called_once()
        _, kwargs = ToolMock.call_args
        assert kwargs["name"] == "finance_tools"
        assert kwargs["command"] == "/usr/bin/python3"
        assert kwargs["args"] == [str(settings.mcp_finance_server_path)]
        assert tool is ToolMock.return_value


def test_build_finance_mcp_tool_requires_server_path(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.delenv("MCP_FINANCE_SERVER_PATH", raising=False)
    import pytest
    with pytest.raises(ValueError):
        build_finance_mcp_tool(Settings())
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_mcp_finance.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `mcp_finance.py`**

```python
# src/ms_agent_app/mcp_finance.py
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from agent_framework import MCPStdioTool

from .config import Settings


def build_finance_mcp_tool(settings: Settings) -> MCPStdioTool:
    """Construct an MCPStdioTool that spawns the local financial MCP server.

    Caller is responsible for entering the async context (`async with tool: ...`).
    """
    if settings.mcp_finance_server_path is None:
        raise ValueError("MCP_FINANCE_SERVER_PATH must be set to attach the finance MCP server.")
    if not settings.mcp_finance_server_path.exists():
        raise FileNotFoundError(
            f"MCP server script not found at {settings.mcp_finance_server_path}"
        )
    return MCPStdioTool(
        name="finance_tools",
        command=settings.mcp_python(),
        args=[str(settings.mcp_finance_server_path)],
    )


@asynccontextmanager
async def open_finance_mcp_tool(settings: Settings) -> AsyncIterator[MCPStdioTool]:
    """Async context-manager wrapping `MCPStdioTool` for clean shutdown."""
    tool = build_finance_mcp_tool(settings)
    async with tool as live:
        yield live
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_mcp_finance.py -v
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add src/ms_agent_app/mcp_finance.py tests/test_mcp_finance.py
git commit -m "feat(mcp): wire MCPStdioTool to local finance server"
```

### Task 2.3: End-to-end smoke run with tools

- [ ] **Step 1: Run the CLI with MCP attached**

```bash
uv run ms-agent-app --with-mcp
```

Expected: REPL opens, no traceback. Try:

```
you> What tools do you have available?
you> Run a dual moving average analysis on AAPL.
```

You should see the agent enumerate tools (drawn from `tool_registry.py`) and make at least one tool call for the AAPL query. If the agent says "I have no tools", confirm `MCP_FINANCE_SERVER_PATH` is correct and the subprocess is alive (check `ps aux | grep main.py`).

- [ ] **Step 2: Manual checklist**

Verify:

- [ ] Subprocess starts only when `--with-mcp` is set (no extra `python main.py` running in chat-only mode).
- [ ] Subprocess exits when the REPL exits (no orphan process after `exit`).

- [ ] **Step 3: Commit any tweaks discovered during smoke-run**

```bash
git add -p && git commit -m "fix(mcp): <describe>"
```

(Skip if nothing changed.)

---

## Phase 3 — Evaluation with Azure AI Evaluation SDK

The SDK's evaluators (`IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator`) accept OpenAI-style message lists. We capture trajectories during a scripted run, then feed them to the evaluators.

### Task 3.1: Dataset of curated prompts

**Files:**
- Create: `src/ms_agent_app/eval/__init__.py`
- Create: `src/ms_agent_app/eval/dataset.py`

- [ ] **Step 1: Implement `dataset.py`**

```python
# src/ms_agent_app/eval/__init__.py
"""Evaluation harness for ms-agent-app."""
```

```python
# src/ms_agent_app/eval/dataset.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    prompt: str
    expected_intent: str
    expects_tool_call: bool
    notes: Optional[str] = None


CASES: tuple[EvalCase, ...] = (
    EvalCase(
        case_id="intent-direct",
        prompt="In one sentence, what is the Microsoft Agent Framework?",
        expected_intent="Definition / explanation of MS Agent Framework",
        expects_tool_call=False,
    ),
    EvalCase(
        case_id="tool-dual-ma",
        prompt="Run a dual moving average backtest on AAPL for the last 2 years.",
        expected_intent="Quantitative analysis using finance tools",
        expects_tool_call=True,
    ),
    EvalCase(
        case_id="tool-fundamentals",
        prompt="Give me the latest fundamental analysis snapshot for MSFT.",
        expected_intent="Fundamental analysis lookup",
        expects_tool_call=True,
    ),
    EvalCase(
        case_id="clarification",
        prompt="Help me with a strategy.",
        expected_intent="Ambiguous — agent should ask for clarification.",
        expects_tool_call=False,
        notes="Tests intent resolution under ambiguity.",
    ),
)
```

- [ ] **Step 2: Commit**

```bash
git add src/ms_agent_app/eval/__init__.py src/ms_agent_app/eval/dataset.py
git commit -m "feat(eval): curated evaluation dataset"
```

### Task 3.2: Trajectory runner (records OpenAI-shape messages + tool calls)

**Files:**
- Create: `src/ms_agent_app/eval/runner.py`
- Test: `tests/test_eval_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_eval_runner.py
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ms_agent_app.eval.runner import to_query_messages, to_response_messages, Trajectory


def test_to_query_messages_wraps_text_in_openai_schema():
    msgs = to_query_messages("hello there")
    assert msgs == [
        {"role": "user", "content": [{"type": "text", "text": "hello there"}]}
    ]


def test_to_response_messages_handles_plain_text():
    msgs = to_response_messages(text="hi back", tool_calls=[])
    assert msgs == [
        {"role": "assistant", "content": [{"type": "text", "text": "hi back"}]}
    ]


def test_to_response_messages_includes_tool_calls():
    msgs = to_response_messages(
        text="done",
        tool_calls=[{"tool_name": "finance_tools.dual_ma", "arguments": {"symbol": "AAPL"}}],
    )
    # one assistant message with tool_calls + text
    assert msgs[0]["role"] == "assistant"
    assert any(c["type"] == "tool_call" for c in msgs[0]["content"])
    assert any(c["type"] == "text" for c in msgs[0]["content"])


@pytest.mark.asyncio
async def test_trajectory_records_run():
    fake_agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(
        text="42",
        tool_calls=[],
    )))
    traj = Trajectory(case_id="t", prompt="what is 6*7?")
    await traj.record(fake_agent)
    assert traj.response_text == "42"
    assert traj.query_messages[0]["role"] == "user"
    assert traj.response_messages[0]["role"] == "assistant"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_eval_runner.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `runner.py`**

```python
# src/ms_agent_app/eval/runner.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


def to_query_messages(text: str) -> list[dict[str, Any]]:
    return [{"role": "user", "content": [{"type": "text", "text": text}]}]


def to_response_messages(
    *,
    text: str,
    tool_calls: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for call in tool_calls:
        content.append({
            "type": "tool_call",
            "tool_call_id": call.get("id", call.get("tool_name", "tool_call")),
            "name": call.get("tool_name"),
            "arguments": call.get("arguments", {}),
        })
    if text:
        content.append({"type": "text", "text": text})
    return [{"role": "assistant", "content": content}]


@dataclass
class Trajectory:
    case_id: str
    prompt: str
    response_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def query_messages(self) -> list[dict[str, Any]]:
        return to_query_messages(self.prompt)

    @property
    def response_messages(self) -> list[dict[str, Any]]:
        return to_response_messages(text=self.response_text, tool_calls=self.tool_calls)

    async def record(self, agent, *, tools=None) -> None:
        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools
        result = await agent.run(self.prompt, **kwargs)
        self.response_text = getattr(result, "text", "") or str(result)
        raw_calls = getattr(result, "tool_calls", None) or []
        normalized: list[dict[str, Any]] = []
        for call in raw_calls:
            normalized.append({
                "id": getattr(call, "id", None) or getattr(call, "tool_call_id", None),
                "tool_name": getattr(call, "name", None) or getattr(call, "tool_name", None),
                "arguments": getattr(call, "arguments", None) or {},
            })
        self.tool_calls = normalized
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_eval_runner.py -v
```

Expected: all 4 pass.

- [ ] **Step 5: Commit**

```bash
git add src/ms_agent_app/eval/runner.py tests/test_eval_runner.py
git commit -m "feat(eval): trajectory recorder in OpenAI message schema"
```

### Task 3.3: Score with Azure AI Evaluation SDK

**Files:**
- Create: `src/ms_agent_app/eval/score.py`

- [ ] **Step 1: Implement `score.py`**

```python
# src/ms_agent_app/eval/score.py
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from azure.ai.evaluation import (
    AzureOpenAIModelConfiguration,
    IntentResolutionEvaluator,
    TaskAdherenceEvaluator,
    ToolCallAccuracyEvaluator,
)

from ..agent_factory import build_chat_agent
from ..config import Settings
from ..mcp_finance import open_finance_mcp_tool
from .dataset import CASES, EvalCase
from .runner import Trajectory


def _model_config(settings: Settings) -> AzureOpenAIModelConfiguration:
    missing = [
        name for name, val in (
            ("AZURE_DEPLOYMENT_NAME", settings.azure_deployment_name),
            ("AZURE_API_KEY", settings.azure_api_key),
            ("AZURE_ENDPOINT", settings.azure_endpoint),
        ) if not val
    ]
    if missing:
        raise SystemExit(f"Missing env vars for eval judge: {', '.join(missing)}")
    return AzureOpenAIModelConfiguration(
        azure_endpoint=settings.azure_endpoint,
        api_key=settings.azure_api_key,
        azure_deployment=settings.azure_deployment_name,
        api_version=settings.azure_api_version,
    )


async def _collect_trajectories(settings: Settings, cases: tuple[EvalCase, ...]) -> list[Trajectory]:
    trajectories: list[Trajectory] = []
    async with open_finance_mcp_tool(settings) as mcp_server:
        async with build_chat_agent(settings) as agent:
            for case in cases:
                traj = Trajectory(case_id=case.case_id, prompt=case.prompt)
                await traj.record(agent, tools=mcp_server)
                trajectories.append(traj)
    return trajectories


def _score_one(
    traj: Trajectory,
    case: EvalCase,
    intent_eval,
    task_eval,
    tool_eval,
) -> dict[str, Any]:
    intent = intent_eval(query=traj.query_messages, response=traj.response_messages)
    task = task_eval(query=traj.query_messages, response=traj.response_messages)
    record: dict[str, Any] = {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "response_text": traj.response_text,
        "intent_resolution": intent,
        "task_adherence": task,
    }
    if traj.tool_calls:
        tool = tool_eval(
            query=traj.query_messages,
            response=traj.response_messages,
            tool_calls=traj.tool_calls,
        )
        record["tool_call_accuracy"] = tool
    return record


async def _amain() -> int:
    settings = Settings()
    model_config = _model_config(settings)

    intent_eval = IntentResolutionEvaluator(model_config=model_config, threshold=3)
    task_eval = TaskAdherenceEvaluator(model_config=model_config, threshold=0.5)
    tool_eval = ToolCallAccuracyEvaluator(model_config=model_config)

    trajectories = await _collect_trajectories(settings, CASES)
    results: list[dict[str, Any]] = []
    for traj, case in zip(trajectories, CASES, strict=True):
        results.append(_score_one(traj, case, intent_eval, task_eval, tool_eval))

    out_dir = Path(".eval_outputs")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "results.json"
    out_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"Wrote {out_file}")
    return 0


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-run the evaluation**

Requires `.env` filled (Foundry + judge model + MCP) and `az login`:

```bash
uv run python -m ms_agent_app.eval.score
```

Expected: prints `Wrote .eval_outputs/results.json`. Inspect:

```bash
cat .eval_outputs/results.json | head -40
```

Each case should have `intent_resolution.intent_resolution` (Likert 1-5) and `task_adherence.task_adherence` (0/1 or 0.0/1.0). The `tool-dual-ma` and `tool-fundamentals` cases should also include `tool_call_accuracy.tool_call_accuracy`.

- [ ] **Step 3: Commit**

```bash
git add src/ms_agent_app/eval/score.py
git commit -m "feat(eval): score trajectories with Azure AI Evaluation SDK"
```

### Task 3.4: Final verification pass

- [ ] **Step 1: Lint**

```bash
uv run ruff check . && uv run ruff format --check .
```

Expected: clean. Run `uv run ruff format .` if needed and commit.

- [ ] **Step 2: All tests pass**

```bash
uv run pytest -v
```

Expected: every test in `tests/` passes.

- [ ] **Step 3: Three demos in one terminal**

Verify all three modes still work end-to-end:

```bash
# Phase 1
echo "exit" | uv run ms-agent-app
# Phase 2
echo -e "What tools are available?\nexit" | uv run ms-agent-app --with-mcp
# Phase 3
uv run python -m ms_agent_app.eval.score
```

Expected: no tracebacks, evaluation JSON regenerated.

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A && git commit -m "chore: final verification pass"
```

---

## Out of scope

- Web UI (Streamlit / FastAPI) — chat is CLI-only.
- Multi-agent workflows or handoffs.
- Durable hosting (Azure Functions, container apps).
- Remote MCP servers (we only attach the existing local stdio server).
- CI pipeline — local `uv run pytest` is sufficient.
