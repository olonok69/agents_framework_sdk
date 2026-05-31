"""Interactive CLI entrypoint for the demo agent application.

The CLI supports:
1. Plain chat mode against the configured model provider.
2. MCP-enabled mode (`--with-mcp`) that exposes local finance tools.
3. Runtime provider override (`--provider`).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .agent_factory import build_chat_agent
from .config import Settings


async def _chat_loop(use_mcp: bool, provider: str | None) -> None:
    """Run one interactive chat session.

    If MCP mode is enabled, this function opens the finance MCP tool context,
    then runs the same REPL loop while passing tools to `agent.run(...)`.
    """
    settings = Settings()
    # CLI flag takes precedence over MODEL_PROVIDER from environment.
    selected_provider = provider or settings.model_provider

    if use_mcp:
        # Imported lazily so Phase 1 doesn't require MCP wiring to import.
        from .mcp_finance import open_finance_mcp_tool

        async with open_finance_mcp_tool(settings) as mcp_server:
            async with build_chat_agent(settings, provider=selected_provider) as agent:
                await _repl(agent, tools=mcp_server)
    else:
        async with build_chat_agent(settings, provider=selected_provider) as agent:
            await _repl(agent, tools=None)


async def _repl(agent, tools) -> None:
    """Run a minimal terminal REPL over the provided agent.

    The function keeps prompting for user input until EOF or a quit command,
    and prints the text form of each model response.
    """
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
        # Pass tools only when MCP mode is active; keep plain-chat path minimal.
        kwargs = {"tools": tools} if tools is not None else {}
        result = await agent.run(user, **kwargs)
        text = getattr(result, "text", None) or str(result)
        print(f"agent> {text}")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and execute the async chat loop.

    Returns a process-style exit code:
    - `0` for normal completion.
    - `130` when interrupted via Ctrl+C.
    """
    parser = argparse.ArgumentParser(prog="ms-agent-app")
    parser.add_argument("--with-mcp", action="store_true", help="Attach local finance MCP server.")
    parser.add_argument(
        "--provider",
        choices=["foundry", "openai", "azure-openai", "anthropic"],
        default=None,
        help="Model provider override. Defaults to MODEL_PROVIDER from environment.",
    )
    args = parser.parse_args(argv)
    try:
        asyncio.run(_chat_loop(args.with_mcp, args.provider))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
