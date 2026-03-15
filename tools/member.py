"""Member management MCP tools (merged from admin_member + shared_query member parts)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, require_self_or_manager, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post, api_put, api_delete


# ============================================================
# Member CRUD
# ============================================================

@register_tool
async def list_members(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """列出项目所有成员。"""
    require_login(session_id)
    return await api_get(f"/projects/{project_id}/members", session_id=session_id)


@register_tool
async def get_member(member_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取成员详情。"""
    require_login(session_id)
    return await api_get(f"/members/{member_id}", session_id=session_id)


@register_tool
async def add_member(
    project_id: str,
    name: str,
    contact: str | None = None,
    responsibility: str | None = None,
    max_workload: float = 40.0,
    availability_status: str = "Available",
    feishu_user_id: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """添加成员到项目（需要项目 Owner 或 Admin）。"""
    await require_project_manager(session_id, project_id)
    payload: dict = {"name": name, "max_workload": max_workload, "availability_status": availability_status}
    if contact is not None:
        payload["contact"] = contact
    if responsibility is not None:
        payload["responsibility"] = responsibility
    if feishu_user_id is not None:
        payload["feishu_user_id"] = feishu_user_id
    return await api_post(f"/projects/{project_id}/members", json=payload, session_id=session_id)


@register_tool
async def update_member(
    member_id: str,
    name: str | None = None,
    contact: str | None = None,
    responsibility: str | None = None,
    workload: float | None = None,
    max_workload: float | None = None,
    availability_status: str | None = None,
    feishu_user_id: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新成员信息（本人、项目 Owner 或 Admin）。availability_status 可选值：Available, Busy, OnLeave, Offline。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {}
    for key in ("name", "contact", "responsibility", "workload", "max_workload",
                "availability_status", "feishu_user_id"):
        val = locals()[key]
        if val is not None:
            payload[key] = val
    return await api_put(f"/members/{member_id}", json=payload, session_id=session_id)


@register_tool
async def remove_member(member_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """移除成员（需要项目 Owner 或 Admin）。"""
    # 后端会检查 require_project_manager
    require_login(session_id)
    return await api_delete(f"/members/{member_id}", session_id=session_id)


# ============================================================
# Skills
# ============================================================

@register_tool
async def list_member_skills(member_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """查看成员技能列表。"""
    require_login(session_id)
    return await api_get(f"/members/{member_id}/skills", session_id=session_id)


@register_tool
async def add_member_skill(
    member_id: str,
    skill_name: str,
    skill_description: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """为成员添加技能（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {"skill_name": skill_name}
    if skill_description is not None:
        payload["skill_description"] = skill_description
    return await api_post(f"/members/{member_id}/skills", json=payload, session_id=session_id)


@register_tool
async def remove_member_skill(member_id: str, skill_id: int, session_id: str = DEFAULT_SESSION) -> dict:
    """移除成员技能（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    return await api_delete(f"/members/{member_id}/skills/{skill_id}", session_id=session_id)


# ============================================================
# Availability Overrides (formerly Windows)
# ============================================================

@register_tool
async def list_availability_windows(member_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """列出成员的可用时间覆盖（临时覆盖）。"""
    require_login(session_id)
    return await api_get(f"/members/{member_id}/availability-overrides", session_id=session_id)


@register_tool
async def add_availability_window(
    member_id: str,
    start_time: str,
    end_time: str,
    status: str = "Available",
    reason: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """为成员新增可用时间覆盖（本人、项目 Owner 或 Admin）。status 可选值：Available, Busy, OnLeave, Offline。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {"start_time": start_time, "end_time": end_time, "status": status}
    if reason is not None:
        payload["reason"] = reason
    return await api_post(f"/members/{member_id}/availability-overrides", json=payload, session_id=session_id)


@register_tool
async def update_availability_window(
    member_id: str,
    window_id: int,
    start_time: str | None = None,
    end_time: str | None = None,
    status: str | None = None,
    reason: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新成员的可用时间覆盖（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {}
    for key in ("start_time", "end_time", "status", "reason"):
        val = locals()[key]
        if val is not None:
            payload[key] = val
    return await api_put(f"/members/{member_id}/availability-overrides/{window_id}", json=payload, session_id=session_id)


@register_tool
async def remove_availability_window(
    member_id: str,
    window_id: int,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """删除成员的可用时间覆盖（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    return await api_delete(f"/members/{member_id}/availability-overrides/{window_id}", session_id=session_id)


# ============================================================
# Availability Patterns (recurring)
# ============================================================

@register_tool
async def list_availability_patterns(member_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """列出成员的周期性可用时间模式。"""
    require_login(session_id)
    return await api_get(f"/members/{member_id}/availability-patterns", session_id=session_id)


@register_tool
async def add_availability_pattern(
    member_id: str,
    day_of_week: int,
    start_time: str,
    end_time: str,
    timezone: str = "Asia/Shanghai",
    status: str = "Available",
    reason: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """为成员新增周期性可用时间模式（本人、项目 Owner 或 Admin）。day_of_week: 0=Monday, 6=Sunday。start_time/end_time 格式: HH:MM。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": timezone,
        "status": status,
    }
    if reason is not None:
        payload["reason"] = reason
    return await api_post(f"/members/{member_id}/availability-patterns", json=payload, session_id=session_id)


@register_tool
async def update_availability_pattern(
    member_id: str,
    pattern_id: int,
    day_of_week: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    timezone: str | None = None,
    status: str | None = None,
    reason: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新成员的周期性可用时间模式（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    payload: dict = {}
    for key in ("day_of_week", "start_time", "end_time", "timezone", "status", "reason"):
        val = locals()[key]
        if val is not None:
            payload[key] = val
    return await api_put(f"/members/{member_id}/availability-patterns/{pattern_id}", json=payload, session_id=session_id)


@register_tool
async def remove_availability_pattern(
    member_id: str,
    pattern_id: int,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """删除成员的周期性可用时间模式（本人、项目 Owner 或 Admin）。"""
    await require_self_or_manager(session_id, member_id)
    return await api_delete(f"/members/{member_id}/availability-patterns/{pattern_id}", session_id=session_id)
