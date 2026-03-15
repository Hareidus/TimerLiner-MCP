"""Decision MCP tools: validate and apply decisions (merged from admin_decision)."""

from typing import Any

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_project_manager, DEFAULT_SESSION
from mcp_server.http_client import api_post


@register_tool
async def validate_decision(
    project_id: str,
    decision_type: str,
    changes: list[dict[str, Any]],
    required_skills_by_task: dict[str, list[str]] | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """验证决策（检查循环依赖、过载、技能不匹配）（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    payload: dict = {"project_id": project_id, "decision_type": decision_type, "changes": changes}
    if required_skills_by_task is not None:
        payload["required_skills_by_task"] = required_skills_by_task
    return await api_post("/decision/validate", json=payload, session_id=session_id)


@register_tool
async def apply_decision(
    project_id: str,
    decision_type: str,
    changes: list[dict[str, Any]],
    required_skills_by_task: dict[str, list[str]] | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """应用决策（更新任务 + 重算 CPM）（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    payload: dict = {"project_id": project_id, "decision_type": decision_type, "changes": changes}
    if required_skills_by_task is not None:
        payload["required_skills_by_task"] = required_skills_by_task
    return await api_post("/decision/apply", json=payload, session_id=session_id)
