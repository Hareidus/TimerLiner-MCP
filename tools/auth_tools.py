"""Authentication MCP tools: login, get_current_user."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import set_session, require_login, is_logged_in, DEFAULT_SESSION
from mcp_server.http_client import api_post, api_get


@register_tool
async def login(username: str, password: str, session_id: str = DEFAULT_SESSION) -> dict:
    """手动登录（通常不需要，连接时已通过环境变量自动登录）。可用于切换用户身份。"""
    resp = await api_post("/auth/login", json={"username": username, "password": password}, session_id=session_id)
    user = resp["user"]
    set_session(
        session_id,
        token=resp["access_token"],
        user_id=user["id"],
        role=user["role"],
        display_name=user["display_name"],
    )
    return {"message": f"登录成功，欢迎 {user['display_name']} ({user['role']})", "user": user}


@register_tool
async def get_current_user(session_id: str = DEFAULT_SESSION) -> dict:
    """获取当前登录用户信息。"""
    require_login(session_id)
    resp = await api_get("/auth/me", session_id=session_id)
    return resp
