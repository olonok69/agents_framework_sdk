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
