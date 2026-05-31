"""MCP integration helpers for the local finance tool server.

This module handles subprocess wiring and lifecycle management for the stdio
MCP server consumed by the agent.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agent_framework import MCPStdioTool

from .config import Settings


def build_finance_mcp_tool(settings: Settings) -> MCPStdioTool:
    """Construct an MCPStdioTool that spawns the local financial MCP server.

    Caller is responsible for entering the async context (`async with tool: ...`).
    """
    if settings.mcp_finance_server_path is None:
        raise ValueError("MCP_FINANCE_SERVER_PATH must be set to attach the finance MCP server.")
    if not settings.mcp_finance_server_path.exists():
        # Fail early with an explicit path error before spawning subprocess.
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
    # Ensure subprocess startup/shutdown is tied to the caller's async context.
    async with tool as live:
        yield live
