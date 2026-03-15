"""Milestone management MCP tools (merged from admin_milestone + shared_query milestone parts)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post, api_put, api_delete


@register_tool
async def list_milestones(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """列出项目所有里程碑。"""
    require_login(session_id)
    return await api_get(f"/projects/{project_id}/milestones", session_id=session_id)


@register_tool
async def get_milestone(milestone_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取里程碑详情。"""
    require_login(session_id)
    return await api_get(f"/milestones/{milestone_id}", session_id=session_id)


@register_tool
async def create_milestone(
    project_id: str,
    name: str,
    target_date: str,
    description: str | None = None,
    task_ids: list[str] | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """创建里程碑（需要项目 Owner 或 Admin）。target_date 格式: ISO8601。"""
    await require_project_manager(session_id, project_id)
    payload: dict = {"name": name, "target_date": target_date, "task_ids": task_ids or []}
    if description is not None:
        payload["description"] = description
    return await api_post(f"/projects/{project_id}/milestones", json=payload, session_id=session_id)


@register_tool
async def update_milestone(
    milestone_id: str,
    name: str | None = None,
    description: str | None = None,
    target_date: str | None = None,
    task_ids: list[str] | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新里程碑（需要项目 Owner 或 Admin）。"""
    # 后端会检查 require_project_manager
    require_login(session_id)
    payload: dict = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if target_date is not None:
        payload["target_date"] = target_date
    if task_ids is not None:
        payload["task_ids"] = task_ids
    return await api_put(f"/milestones/{milestone_id}", json=payload, session_id=session_id)


@register_tool
async def delete_milestone(milestone_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """删除里程碑（需要项目 Owner 或 Admin）。"""
    require_login(session_id)
    return await api_delete(f"/milestones/{milestone_id}", session_id=session_id)
