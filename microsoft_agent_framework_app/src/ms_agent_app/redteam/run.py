"""Run a PyRIT red-team pass against the Foundry-backed Agent.

Mirrors the structure of `ms_agent_app.eval.score`:

  1. Load env via `Settings`.
  2. Build the same Foundry-backed Agent the chat CLI uses.
  3. Wrap the Agent in an `AgentFrameworkTarget`.
  4. Score each prompt with `SelfAskRefusalScorer` (Azure OpenAI judge).
  5. Write `.pyrit_outputs/results.json` with one record per case.

`pyrit` and its judge target are imported lazily inside the runtime so the
package can be installed as an optional extra (`uv sync --extra redteam`).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from ..agent_factory import build_chat_agent
from ..config import Settings
from .dataset import CASES, RedTeamCase
from .target import AgentFrameworkTarget


def _require_judge_env(settings: Settings) -> None:
    """Validate environment variables required by the configured judge provider."""
    if settings.judge_provider == "azure-openai":
        # Azure judge path requires endpoint + deployment + API key tuple.
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
            raise SystemExit(
                "Missing env vars for PyRIT judge model (azure-openai): " + ", ".join(missing)
            )
        return

    missing = [
        name
        for name, val in (
            ("JUDGE_OPENAI_API_KEY or OPENAI_API_KEY", settings.judge_openai_api_key or settings.openai_api_key),
            (
                "JUDGE_OPENAI_MODEL or OPENAI_CHAT_MODEL or OPENAI_MODEL",
                settings.judge_openai_model or settings.openai_chat_model or settings.openai_model,
            ),
        )
        if not val
    ]
    if missing:
        raise SystemExit("Missing env vars for PyRIT judge model (openai): " + ", ".join(missing))


def _build_judge_target(settings: Settings) -> Any:
    """Construct an `OpenAIChatTarget` for the configured judge provider."""
    from pyrit.prompt_target import OpenAIChatTarget

    if settings.judge_provider == "azure-openai":
        # PyRIT OpenAI target expects Azure endpoint in `/openai/v1` shape.
        endpoint = (settings.azure_endpoint or "").rstrip("/") + "/openai/v1"
        api_key = settings.azure_api_key
        model = settings.azure_deployment_name
    else:
        # Default to OpenAI public base URL when no override is configured.
        endpoint = (settings.judge_openai_base_url or settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        api_key = settings.judge_openai_api_key or settings.openai_api_key
        model = settings.judge_openai_model or settings.openai_chat_model or settings.openai_model

    return OpenAIChatTarget(
        endpoint=endpoint,
        api_key=api_key,
        model_name=model,
    )


def _serialize_completed(case: RedTeamCase, attack_result: Any) -> dict[str, Any]:
    last_response = getattr(attack_result, "last_response", None)
    response_text = getattr(last_response, "converted_value", None) or getattr(
        last_response, "original_value", ""
    )
    last_score = getattr(attack_result, "last_score", None)
    score_value = getattr(last_score, "score_value", None)
    score_rationale = getattr(last_score, "score_rationale", None)
    outcome = getattr(attack_result, "outcome", None)
    outcome_name = outcome.name if outcome is not None else None
    # SelfAskRefusalScorer's objective is "detect a refusal".
    # SUCCESS  → refusal detected (the defense held)
    # FAILURE  → no refusal detected (agent complied with the attack — true positive jailbreak)
    # anything else → undetermined
    if outcome_name == "SUCCESS":
        refusal_detected = True
    elif outcome_name == "FAILURE":
        refusal_detected = False
    else:
        refusal_detected = None
    return {
        "case_id": case.case_id,
        "category": case.category,
        "objective": case.objective,
        "agent_response": response_text,
        "outcome": outcome_name,
        "refusal_detected": refusal_detected,
        "score_value": score_value,
        "score_rationale": score_rationale,
        "outcome_reason": getattr(attack_result, "outcome_reason", None),
    }


def _serialize_incomplete(case: RedTeamCase, exc: BaseException) -> dict[str, Any]:
    """Record per-case failures (e.g. Azure content-filter 400) without aborting the pass."""
    msg = str(exc)
    blocked_at_filter = "content_filter" in msg or "responsible AI" in msg.lower()
    return {
        "case_id": case.case_id,
        "category": case.category,
        "objective": case.objective,
        "agent_response": None,
        "outcome": "BLOCKED_AT_FILTER" if blocked_at_filter else "ERROR",
        "refusal_detected": True if blocked_at_filter else None,
        "score_value": None,
        "score_rationale": None,
        "outcome_reason": msg[:2000],
    }


async def _amain() -> int:
    """Run the full red-team workflow and write results to disk."""
    settings = Settings()
    _require_judge_env(settings)
    print(f"PyRIT judge provider: {settings.judge_provider}")

    from pyrit.executor.attack import (
        AttackExecutor,
        AttackScoringConfig,
        PromptSendingAttack,
    )
    from pyrit.score import SelfAskRefusalScorer
    from pyrit.setup import IN_MEMORY, initialize_pyrit_async

    # Keep runtime self-contained by using in-memory PyRIT storage for this demo.
    await initialize_pyrit_async(IN_MEMORY)

    judge_target = _build_judge_target(settings)
    refusal_scorer = SelfAskRefusalScorer(chat_target=judge_target)

    async with build_chat_agent(settings) as agent:
        target = AgentFrameworkTarget(agent)
        attack = PromptSendingAttack(
            objective_target=target,
            attack_scoring_config=AttackScoringConfig(objective_scorer=refusal_scorer),
        )
        executor = AttackExecutor(max_concurrency=2)
        bundle = await executor.execute_attack_async(
            attack=attack,
            objectives=[case.objective for case in CASES],
            return_partial_on_failure=True,
        )

    results: list[dict[str, Any] | None] = [None] * len(CASES)
    # completed_results may be shorter than CASES if some inputs failed; input_indices
    # maps each completed result back to its original case index.
    for completed_idx, case_idx in enumerate(bundle.input_indices):
        # Re-map completed outputs back to original case indices.
        results[case_idx] = _serialize_completed(
            CASES[case_idx], bundle.completed_results[completed_idx]
        )
    # incomplete_objectives carry (objective_text, exception) tuples — match back by text.
    objective_to_case = {case.objective: case for case in CASES}
    for objective_text, exc in bundle.incomplete_objectives:
        # Preserve per-case failure records instead of aborting the full run.
        case = objective_to_case.get(objective_text)
        if case is None:
            continue
        results[CASES.index(case)] = _serialize_incomplete(case, exc)

    out_dir = Path(".pyrit_outputs")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "results.json"
    out_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"Wrote {out_file}")

    refusals = sum(1 for r in results if r and r.get("refusal_detected"))
    print(f"Refusal / block detected on {refusals}/{len(results)} attack cases.")
    return 0


def main() -> int:
    """CLI entrypoint for `python -m ms_agent_app.redteam.run`."""
    return asyncio.run(_amain())


if __name__ == "__main__":
    sys.exit(main())
