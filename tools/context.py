"""Context MCP tools: project context, task context, activities (from shared_context)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, DEFAULT_SESSION
from mcp_server.http_client import api_get


@register_tool
async def get_project_context(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取项目 Markdown 上下文（包含任务列表、成员列表、关键路径等），适合喂给 LLM。"""
    require_login(session_id)
    return await api_get(f"/context/project/{project_id}", session_id=session_id)


@register_tool
async def get_task_context(task_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取任务 Markdown 上下文（包含负责人、依赖关系、调度信息等）。"""
    require_login(session_id)
    return await api_get(f"/context/task/{task_id}", session_id=session_id)


@register_tool
async def get_project_activities(
    project_id: str,
    limit: int = 20,
    offset: int = 0,
    event_type: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """获取项目活动日志（任务完成、里程碑达成、事件记录等）。"""
    require_login(session_id)
    params: dict = {"limit": limit, "offset": offset}
    if event_type:
        params["event_type"] = event_type
    return await api_get(f"/projects/{project_id}/activities", session_id=session_id, params=params)
