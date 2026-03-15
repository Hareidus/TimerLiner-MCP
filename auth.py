"""Session management and role checking for MCP Server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

# In-memory session store keyed by session_id
_sessions: dict[str, "Session"] = {}

# Default session id used when MCP is single-user
DEFAULT_SESSION = "default"


@dataclass
class Session:
    token: str = ""
    user_id: str = ""
    role: str = ""
    display_name: str = ""


def get_session(session_id: str = DEFAULT_SESSION) -> Session:
    if session_id not in _sessions:
        _sessions[session_id] = Session()
    return _sessions[session_id]


def set_session(
    session_id: str = DEFAULT_SESSION,
    *,
    token: str,
    user_id: str,
    role: str,
    display_name: str,
) -> Session:
    session = Session(token=token, user_id=user_id, role=role, display_name=display_name)
    _sessions[session_id] = session
    return session


def clear_session(session_id: str = DEFAULT_SESSION) -> None:
    _sessions.pop(session_id, None)


def is_logged_in(session_id: str = DEFAULT_SESSION) -> bool:
    return bool(get_session(session_id).token)


def require_login(session_id: str = DEFAULT_SESSION) -> Session:
    session = get_session(session_id)
    if not session.token:
        raise PermissionError("未登录，请配置 TIMELINER_USERNAME 和 TIMELINER_PASSWORD 环境变量")
    return session


def require_admin(session_id: str = DEFAULT_SESSION) -> Session:
    session = require_login(session_id)
    if session.role != "Admin":
        raise PermissionError("需要 Admin 权限")
    return session


async def require_project_manager(session_id: str, project_id: str) -> Session:
    """Admin 或项目 Owner 可通过。"""
    from mcp_server.http_client import api_get

    session = require_login(session_id)
    if session.role == "Admin":
        return session
    resp = await api_get(f"/projects/{project_id}/members", session_id=session_id)
    for m in resp.get("data", []):
        if m.get("user_id") == session.user_id and m.get("project_role") == "Owner":
            return session
    raise PermissionError("需要项目 Owner 或 Admin 权限")


async def require_self_or_manager(session_id: str, member_id: str) -> Session:
    """本人、项目 Owner 或 Admin 可通过。"""
    from mcp_server.http_client import api_get

    session = require_login(session_id)
    if session.role == "Admin":
        return session
    resp = await api_get(f"/members/{member_id}", session_id=session_id)
    member = resp.get("data", {})
    if member.get("user_id") == session.user_id:
        return session
    project_id = member.get("project_id")
    members_resp = await api_get(f"/projects/{project_id}/members", session_id=session_id)
    for m in members_resp.get("data", []):
        if m.get("user_id") == session.user_id and m.get("project_role") == "Owner":
            return session
    raise PermissionError("只能操作自己的信息，或需要 Owner/Admin 权限")


async def auto_login() -> None:
    """在 MCP Server 启动时，使用环境变量中的凭据自动登录。"""
    from mcp_server.config import BACKEND_BASE_URL, REQUEST_TIMEOUT, AUTH_USERNAME, AUTH_PASSWORD

    if not AUTH_USERNAME or not AUTH_PASSWORD:
        return

    if is_logged_in():
        return

    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(
            "/auth/login",
            json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
        )
        resp.raise_for_status()
        data = resp.json()

    user = data["user"]
    set_session(
        DEFAULT_SESSION,
        token=data["access_token"],
        user_id=user["id"],
        role=user["role"],
        display_name=user["display_name"],
    )
