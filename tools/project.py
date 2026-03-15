"""Project management MCP tools (merged from admin_project + shared_query project parts)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post, api_put, api_delete


@register_tool
async def list_projects(session_id: str = DEFAULT_SESSION) -> dict:
    """列出所有项目。"""
    require_login(session_id)
    return await api_get("/projects", session_id=session_id)


@register_tool
async def get_project(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取项目详情。"""
    require_login(session_id)
    return await api_get(f"/projects/{project_id}", session_id=session_id)


@register_tool
async def get_project_dashboard(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取项目完整时间线仪表盘（包含 summary、tasks、members、milestones、critical_path）。"""
    require_login(session_id)
    return await api_get(f"/projects/{project_id}/timeline", session_id=session_id)


@register_tool
async def create_project(
    name: str,
    start_time: str,
    deadline: str,
    description: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """创建新项目。start_time/deadline 格式: ISO8601。创建者自动成为项目 Owner。"""
    require_login(session_id)
    payload: dict = {"name": name, "start_time": start_time, "deadline": deadline}
    if description is not None:
        payload["description"] = description
    return await api_post("/projects", json=payload, session_id=session_id)


@register_tool
async def update_project(
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    start_time: str | None = None,
    deadline: str | None = None,
    status: str | None = None,
    progress: float | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新项目信息（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    payload: dict = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if start_time is not None:
        payload["start_time"] = start_time
    if deadline is not None:
        payload["deadline"] = deadline
    if status is not None:
        payload["status"] = status
    if progress is not None:
        payload["progress"] = progress
    return await api_put(f"/projects/{project_id}", json=payload, session_id=session_id)


@register_tool
async def delete_project(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """删除项目（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    return await api_delete(f"/projects/{project_id}", session_id=session_id)
