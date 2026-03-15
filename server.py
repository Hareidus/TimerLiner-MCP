"""TimeLiner MCP Server — low-level mcp.server.Server + tool_registry wiring."""

from mcp.server import Server
from mcp.types import Tool, TextContent

from mcp_server.tool_registry import get_all_tools, call_tool

server = Server("TimeLiner")


def register_all_tools() -> None:
    """Import all tool modules so their @register_tool decorators fire."""
    import mcp_server.tools.auth_tools  # noqa: F401
    import mcp_server.tools.project  # noqa: F401
    import mcp_server.tools.task  # noqa: F401
    import mcp_server.tools.member  # noqa: F401
    import mcp_server.tools.milestone  # noqa: F401
    import mcp_server.tools.schedule  # noqa: F401
    import mcp_server.tools.decision  # noqa: F401
    import mcp_server.tools.invitation  # noqa: F401
    import mcp_server.tools.context  # noqa: F401
    import mcp_server.tools.ai_task_splitting  # noqa: F401


# Register the whoami tool directly (was in old server.py)
from mcp_server.tool_registry import register_tool
from mcp_server.auth import get_session, DEFAULT_SESSION


@register_tool
async def whoami() -> dict:
    """查看当前已登录的用户身份。"""
    session = get_session(DEFAULT_SESSION)
    if not session.token:
        return {"logged_in": False, "message": "未登录"}
    return {
        "logged_in": True,
        "user_id": session.user_id,
        "role": session.role,
        "display_name": session.display_name,
    }


# Wire MCP protocol handlers to the registry
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return get_all_tools()


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    return await call_tool(name, arguments)


# Import all tool modules at module load time
register_all_tools()
