"""Schedule request MCP tools (merged from admin_schedule + user_schedule)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, get_session, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post


@register_tool
async def list_schedule_requests(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """查看项目调度申请列表。"""
    require_login(session_id)
    return await api_get(f"/schedule/projects/{project_id}/requests", session_id=session_id)


@register_tool
async def approve_schedule_request(
    request_id: str,
    project_id: str,
    approved_solution: dict | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """批准调度申请（需要项目 Owner 或 Admin）。"""
    session = await require_project_manager(session_id, project_id)
    payload: dict = {"approver_id": session.user_id}
    if approved_solution is not None:
        payload["approved_solution"] = approved_solution
    return await api_post(f"/schedule/requests/{request_id}/approve", json=payload, session_id=session_id)


@register_tool
async def reject_schedule_request(
    request_id: str,
    project_id: str,
    reject_reason: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """拒绝调度申请（需要项目 Owner 或 Admin）。"""
    session = await require_project_manager(session_id, project_id)
    payload: dict = {"approver_id": session.user_id, "reject_reason": reject_reason}
    return await api_post(f"/schedule/requests/{request_id}/reject", json=payload, session_id=session_id)


@register_tool
async def request_schedule_change(
    project_id: str,
    requester_id: str,
    reason: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """发起调度变更申请。requester_id 为成员 ID。"""
    require_login(session_id)
    return await api_post(
        "/schedule/requests",
        json={"requester_id": requester_id, "reason": reason},
        params={"project_id": project_id},
        session_id=session_id,
    )


@register_tool
async def get_my_schedule_requests(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """查看当前用户的调度申请状态。"""
    session = require_login(session_id)
    resp = await api_get(f"/schedule/projects/{project_id}/requests", session_id=session_id)
    members_resp = await api_get(f"/projects/{project_id}/members", session_id=session_id)
    my_member_ids = {
        m["id"] for m in members_resp.get("data", [])
        if m.get("user_id") == session.user_id or m.get("name") == session.display_name
    }
    my_requests = [r for r in resp.get("data", []) if r.get("requester_id") in my_member_ids]
    return {"success": True, "data": my_requests}


@register_tool
async def request_leave(
    project_id: str,
    requester_id: str,
    start_time: str,
    end_time: str,
    reason: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """提交请假申请。需要项目 Owner/Admin 批准后才能生效。

    start_time/end_time 格式: ISO 8601 格式，如 "2025-03-20T09:00:00Z"
    reason: 请假原因，如"家庭事务"、"病假"等
    """
    require_login(session_id)
    payload = {
        "requester_id": requester_id,
        "reason": reason,
        "request_type": "leave",
        "leave_start_time": start_time,
        "leave_end_time": end_time,
        "leave_status": "OnLeave",
    }
    return await api_post(
        "/schedule/requests",
        json=payload,
        params={"project_id": project_id},
        session_id=session_id,
    )
