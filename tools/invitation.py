"""Invitation management MCP tools (merged from admin_invitation + user_invitation)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post, api_delete


@register_tool
async def create_invitation(
    project_id: str,
    expires_at: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """创建项目邀请码（需要项目 Owner 或 Admin）。expires_at 格式: ISO8601。"""
    await require_project_manager(session_id, project_id)
    return await api_post(
        f"/projects/{project_id}/invitations",
        json={"project_id": project_id, "expires_at": expires_at},
        session_id=session_id,
    )


@register_tool
async def list_invitations(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """查看项目邀请列表。"""
    require_login(session_id)
    resp = await api_get(f"/projects/{project_id}/invitations", session_id=session_id)
    return {"success": True, "data": resp}


@register_tool
async def revoke_invitation(
    invitation_id: str,
    project_id: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """撤销邀请码（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    return await api_delete(f"/invitations/{invitation_id}", session_id=session_id)


@register_tool
async def accept_invitation(invitation_code: str, session_id: str = DEFAULT_SESSION) -> dict:
    """接受邀请加入项目。"""
    require_login(session_id)
    return await api_post(f"/invitations/{invitation_code}/accept", session_id=session_id)
