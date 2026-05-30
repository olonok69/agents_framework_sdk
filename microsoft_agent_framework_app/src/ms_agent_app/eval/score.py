from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from azure.ai.evaluation import (
    OpenAIModelConfiguration,
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


def _model_config(settings: Settings) -> AzureOpenAIModelConfiguration | OpenAIModelConfiguration:
    if settings.judge_provider == "azure-openai":
        missing = [
            name
            for name, val in (
                ("AZURE_DEPLOYMENT_NAME", settings.azure_deployment_name),
                ("AZURE_API_KEY", settings.azure_api_key),
                ("AZURE_ENDPOINT", settings.azure_endpoint),
            )
            if not val
        ]
        if missing:
            raise SystemExit(f"Missing env vars for eval judge (azure-openai): {', '.join(missing)}")
        return AzureOpenAIModelConfiguration(
            type="azure_openai",
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            azure_deployment=settings.azure_deployment_name,
            api_version=settings.azure_api_version,
        )

    api_key = settings.judge_openai_api_key or settings.openai_api_key
    model = settings.judge_openai_model or settings.openai_chat_model or settings.openai_model
    base_url = settings.judge_openai_base_url or settings.openai_base_url or "https://api.openai.com/v1"

    missing = [
        name
        for name, val in (
            ("JUDGE_OPENAI_API_KEY or OPENAI_API_KEY", api_key),
            ("JUDGE_OPENAI_MODEL or OPENAI_CHAT_MODEL or OPENAI_MODEL", model),
        )
        if not val
    ]
    if missing:
        raise SystemExit(f"Missing env vars for eval judge (openai): {', '.join(missing)}")

    config: OpenAIModelConfiguration = {
        "type": "openai",
        "api_key": api_key,
        "model": model,
    }
    config["base_url"] = base_url
    if settings.judge_openai_organization:
        config["organization"] = settings.judge_openai_organization
    return config


def _extract_tool_definitions(mcp_server) -> list[dict[str, Any]]:
    """Pull `{name, description, parameters}` triples from the live MCPStdioTool.

    `mcp_server.functions` is a list of `FunctionTool` whose `parameters` is
    already the JSON-Schema dict expected by `ToolCallAccuracyEvaluator`.
    """
    definitions: list[dict[str, Any]] = []
    for fn in getattr(mcp_server, "functions", None) or []:
        name = getattr(fn, "name", None)
        params_attr = getattr(fn, "parameters", None)
        # FunctionTool.parameters is a method in the agent-framework prerelease;
        # call it if needed, accept it either way.
        params = params_attr() if callable(params_attr) else params_attr
        if not name or not isinstance(params, dict):
            continue
        definitions.append(
            {
                "name": name,
                "description": (getattr(fn, "description", "") or "").strip(),
                "parameters": params,
            }
        )
    return definitions


async def _collect_trajectories(
    settings: Settings, cases: tuple[EvalCase, ...]
) -> tuple[list[Trajectory], list[dict[str, Any]]]:
    trajectories: list[Trajectory] = []
    async with open_finance_mcp_tool(settings) as mcp_server:
        tool_definitions = _extract_tool_definitions(mcp_server)
        async with build_chat_agent(settings) as agent:
            for case in cases:
                traj = Trajectory(case_id=case.case_id, prompt=case.prompt)
                await traj.record(agent, tools=mcp_server)
                trajectories.append(traj)
    return trajectories, tool_definitions


def _score_one(
    traj: Trajectory,
    case: EvalCase,
    intent_eval,
    task_eval,
    tool_eval,
    tool_definitions: list[dict[str, Any]],
) -> dict[str, Any]:
    intent = intent_eval(query=traj.query_messages, response=traj.response_messages)
    task = task_eval(query=traj.query_messages, response=traj.response_messages)
    record: dict[str, Any] = {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "response_text": traj.response_text,
        "tool_calls": traj.tool_calls,
        "intent_resolution": intent,
        "task_adherence": task,
    }
    if traj.tool_calls:
        tool = tool_eval(
            query=traj.query_messages,
            response=traj.response_messages,
            tool_calls=traj.tool_calls,
            tool_definitions=tool_definitions,
        )
        record["tool_call_accuracy"] = tool
    return record


async def _amain() -> int:
    settings = Settings()
    model_config = _model_config(settings)
    print(f"Eval judge provider: {settings.judge_provider}")

    intent_eval = IntentResolutionEvaluator(model_config=model_config, threshold=3)
    task_eval = TaskAdherenceEvaluator(model_config=model_config, threshold=0.5)
    tool_eval = ToolCallAccuracyEvaluator(model_config=model_config)

    trajectories, tool_definitions = await _collect_trajectories(settings, CASES)
    results: list[dict[str, Any]] = []
    for traj, case in zip(trajectories, CASES, strict=True):
        results.append(_score_one(traj, case, intent_eval, task_eval, tool_eval, tool_definitions))

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
