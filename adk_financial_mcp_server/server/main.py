from mcp.server.fastmcp import FastMCP

from tool_registry import register_all_tools

# Initialize FastMCP server
mcp = FastMCP("finance tools", "1.0.0")

register_all_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')