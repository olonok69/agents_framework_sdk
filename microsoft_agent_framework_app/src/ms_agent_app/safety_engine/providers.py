"""Provider abstraction: turn a (provider, model) pair into a stage `target`.

The three live stages each need the target described in their *own* dialect:

    - garak     -> a `--model_type` + `--model_name` pair (it has native
                   `openai`, `azure`, and `litellm` generators)
    - AgentDojo -> an Inspect AI provider-prefixed model string
                   (`azureai/<deployment>`, `google/<model>`, `bedrock/<id>` ...)
    - PyRIT     -> reuses the Phase 4 redteam campaign, which builds the same
                   Microsoft Agent Framework agent the chat CLI uses

`build_target()` is the single place that knows each dialect, so `run.py` and the
stages stay provider-agnostic: flip `--target-provider` and every stage gets the
right wiring. Only **non-secret** identifiers (model/deployment names, generator
types, endpoints) go in the returned dict -- it is serialized verbatim into the
evidence artifact. Credentials stay in the environment, where garak / Inspect /
PyRIT read them directly.

Provider status in this repo:

    demo     zero-config, offline -- the default; no provider wiring needed
    azure    FULLY WIRED -- the PyRIT stage reuses the existing Azure/Foundry
             redteam campaign (redteam/run.py), so it is real end-to-end
    google   scaffolded -- garak via litellm, Inspect via google/, PyRIT not wired
    bedrock  scaffolded -- the original JD target; garak/Inspect set, PyRIT not wired
    openai   scaffolded -- garak/Inspect set, PyRIT not wired

The JD asked for AWS Bedrock; this repo is Azure-native (Foundry, the
azure-openai eval judge, and the redteam path all run on Azure today), so Azure
is the provider we can exercise end-to-end. Bedrock and Google remain a config
change away -- see the per-provider builders below and the README porting note.
"""

from __future__ import annotations

import os


# Providers whose PyRIT stage can reuse the Phase 4 redteam campaign. That
# campaign builds its agent from MODEL_PROVIDER in .env via build_chat_agent,
# which supports foundry/azure and openai (and azure-openai/anthropic). So PyRIT
# runs live for any provider the redteam agent can be, *and* that has a target
# builder here -- i.e. azure, foundry, openai. google/bedrock have no redteam
# agent, so their PyRIT stage skips (see stages.run_pyrit).
#
# NB: the PyRIT stage red-teams the MODEL_PROVIDER agent, not --target-provider.
# Keep them aligned (e.g. --target-provider openai  +  MODEL_PROVIDER=openai),
# or the report mixes two models.
PYRIT_WIRED_PROVIDERS = frozenset({"azure", "foundry", "openai"})


def build_target(provider: str, model: str | None = None, *,
                 demo: bool = False, **overrides) -> dict:
    """Build a stage `target` dict for the given provider.

    Parameters
    ----------
    provider : one of demo | azure | foundry | google | bedrock | openai
    model    : provider model / deployment id; falls back to a provider-specific
               environment variable, then a sensible default
    demo     : when True, return the minimal offline target (no env, no keys)
    overrides: explicit key overrides merged in last (e.g. inspect_model=...)
    """
    provider = (provider or "demo").lower()

    if demo or provider == "demo":
        target = {"provider": "demo", "model": model or "demo-model"}
        target.update(overrides)
        return target

    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ValueError(
            f"unknown target provider '{provider}'; "
            f"valid: {sorted(['demo', *_BUILDERS])}"
        )

    target = builder(model)
    target["provider"] = provider
    # PyRIT only runs live where the redteam campaign target is valid.
    target["pyrit_wired"] = provider in PYRIT_WIRED_PROVIDERS
    target.update(overrides)
    return target


def _azure(model: str | None) -> dict:
    """Azure AI Foundry / Azure OpenAI -- the fully-wired live provider.

    garak ships a native `azure` generator that reads `AZURE_API_KEY`,
    `AZURE_ENDPOINT`, and `AZURE_MODEL_NAME` from the environment; Inspect uses
    the `azureai/<deployment>` model string. The PyRIT stage reuses
    `redteam/run.py`, which builds the Foundry agent from the same `.env`.
    """
    deployment = (
        model
        or os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME")
        or os.getenv("AZURE_OPENAI_CHAT_MODEL")
        or os.getenv("AZURE_DEPLOYMENT_NAME")
        or "gpt-4.1"
    )
    return {
        "model": deployment,
        "garak_model_type": "azure",
        "garak_model_name": deployment,
        "inspect_model": f"azureai/{deployment}",
        "endpoint": os.getenv("AZURE_ENDPOINT") or os.getenv("FOUNDRY_PROJECT_ENDPOINT"),
    }


def _google(model: str | None) -> dict:
    """Google Gemini / Vertex AI -- scaffolded.

    garak reaches Gemini through its `litellm` generator (`gemini/<model>` with
    `GEMINI_API_KEY`, or `vertex_ai/<model>` with ADC); Inspect uses the
    `google/<model>` (Gemini API) or `vertex/<model>` (Vertex) string. The PyRIT
    stage is not wired here -- swap the Foundry agent in redteam/run.py for a
    Gemini-backed agent, or add a Google `PromptTarget`, to light it up.
    """
    name = model or os.getenv("GOOGLE_MODEL") or "gemini-1.5-pro"
    use_vertex = os.getenv("GOOGLE_USE_VERTEX", "").lower() in ("1", "true", "yes")
    litellm_prefix = "vertex_ai" if use_vertex else "gemini"
    inspect_prefix = "vertex" if use_vertex else "google"
    return {
        "model": name,
        "garak_model_type": "litellm",
        "garak_model_name": f"{litellm_prefix}/{name}",
        "inspect_model": f"{inspect_prefix}/{name}",
    }


def _bedrock(model: str | None) -> dict:
    """AWS Bedrock -- the original JD target, scaffolded.

    garak reaches Bedrock through `litellm` (`bedrock/<id>` with standard AWS
    credentials in the environment); Inspect uses the `bedrock/<id>` string. The
    PyRIT stage needs a `BedrockTarget(PromptTarget)` wrapping
    `bedrock-runtime invoke_model` -- see the README porting note. Keep the v0.13
    inversion in mind: `SelfAskRefusalScorer` SUCCESS means refusal *detected*,
    which is NOT a hit.
    """
    name = model or os.getenv("BEDROCK_MODEL_ID") or "anthropic.claude-3-5-sonnet-20240620-v1:0"
    return {
        "model": name,
        "garak_model_type": "litellm",
        "garak_model_name": f"bedrock/{name}",
        "inspect_model": f"bedrock/{name}",
    }


def _openai(model: str | None) -> dict:
    """OpenAI public API -- scaffolded.

    garak has a native `openai` generator (`OPENAI_API_KEY` from env); Inspect
    uses `openai/<model>`. PyRIT not wired here.
    """
    name = model or os.getenv("OPENAI_CHAT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o"
    return {
        "model": name,
        "garak_model_type": "openai",
        "garak_model_name": name,
        "inspect_model": f"openai/{name}",
    }


_BUILDERS = {
    "azure": _azure,
    "foundry": _azure,  # alias -- same Azure wiring
    "google": _google,
    "bedrock": _bedrock,
    "openai": _openai,
}
