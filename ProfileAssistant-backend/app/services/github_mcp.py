import os
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from app.core.config import Config


async def list_github_mcp_tools() -> list[str]:
    """Return the tool names exposed by the connected GitHub MCP server."""
    params = Config.get_github_mcp_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = getattr(response, "tools", []) or []
            return [tool.name for tool in tools if getattr(tool, "name", None)]


async def search_github_projects(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search GitHub via the configured GitHub MCP server.

    This is intentionally defensive: the server may expose different tool names
    depending on the implementation, so we select whichever repo-search tool is
    available and return a clean dictionary to the caller.
    """
    if not query.strip():
        raise ValueError("query must not be empty.")

    params = Config.get_github_mcp_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = getattr(response, "tools", []) or []
            names = [tool.name for tool in tools if getattr(tool, "name", None)]

            search_tool = None
            for candidate in ["search_repositories", "search_repos", "repo_search"]:
                if candidate in names:
                    search_tool = candidate
                    break

            if search_tool is None:
                return {
                    "query": query,
                    "message": "GitHub MCP connected, but no repository search tool was exposed.",
                    "available_tools": names,
                }

            result = await session.call_tool(
                search_tool,
                {"query": query, "per_page": max(1, min(top_k, 10))},
            )

            if hasattr(result, "model_dump"):
                payload = result.model_dump()
            elif hasattr(result, "dict"):
                payload = result.dict()
            else:
                payload = result

            if isinstance(payload, dict) and "content" in payload:
                return {
                    "query": query,
                    "data": payload["content"],
                }

            return {
                "query": query,
                "data": payload,
            }
