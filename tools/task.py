"""Task management MCP tools (merged from admin_task + user_task + shared_query task parts)."""

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_login, require_project_manager, get_session, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post, api_put, api_delete


@register_tool
async def list_tasks(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """列出项目所有任务。"""
    require_login(session_id)
    return await api_get(f"/projects/{project_id}/tasks", session_id=session_id)


@register_tool
async def get_task(task_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取任务详情。"""
    require_login(session_id)
    return await api_get(f"/tasks/{task_id}", session_id=session_id)


@register_tool
async def create_task(
    project_id: str,
    name: str,
    estimated_duration: float,
    description: str | None = None,
    priority: str = "P2",
    owner_id: str | None = None,
    deadline: str | None = None,
    assignees: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """创建单个任务（需要项目 Owner 或 Admin）。

    estimated_duration 单位为小时。
    owner_id 为主负责人（必填，如果有协作者则选择权重最高的作为主负责人）。
    assignees 为 JSON 数组字符串，包含协作者信息，格式：
    [{"member_id": "mem-xxx", "workload_ratio": 0.5, "role": "前端开发"}]

    注意：对于多人协作任务，必须指定 owner_id 作为主负责人，通常选择 workload_ratio 最高的成员。
    """
    await require_project_manager(session_id, project_id)
    payload: dict = {"name": name, "estimated_duration": estimated_duration, "priority": priority}
    if description is not None:
        payload["description"] = description
    if owner_id is not None:
        payload["owner_id"] = owner_id
    if deadline is not None:
        payload["deadline"] = deadline
    if assignees is not None:
        import json
        payload["assignees"] = json.loads(assignees)
    return await api_post(f"/projects/{project_id}/tasks", json=payload, session_id=session_id)


@register_tool
async def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    estimated_duration: float | None = None,
    actual_duration: float | None = None,
    progress: float | None = None,
    owner_id: str | None = None,
    start_time: str | None = None,
    deadline: str | None = None,
    assignees: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新任务信息（项目成员可操作）。

    assignees 为 JSON 数组字符串，包含协作者信息，格式：
    [{"member_id": "mem-xxx", "workload_ratio": 0.5, "role": "前端开发"}]
    """
    require_login(session_id)
    payload: dict = {}
    for key in ("name", "description", "status", "priority", "estimated_duration",
                "actual_duration", "progress", "owner_id", "start_time", "deadline"):
        val = locals()[key]
        if val is not None:
            payload[key] = val
    if assignees is not None:
        import json
        payload["assignees"] = json.loads(assignees)
    return await api_put(f"/tasks/{task_id}", json=payload, session_id=session_id)


@register_tool
async def delete_task(task_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """删除任务（需要项目 Owner 或 Admin）。"""
    require_login(session_id)
    # 后端会检查 require_project_manager
    return await api_delete(f"/tasks/{task_id}", session_id=session_id)


@register_tool
async def add_task_dependency(task_id: str, predecessor_task_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """添加任务依赖关系。task_id 依赖于 predecessor_task_id。"""
    require_login(session_id)
    return await api_post(
        f"/tasks/{task_id}/dependencies",
        json={"predecessor_task_id": predecessor_task_id},
        session_id=session_id,
    )


@register_tool
async def get_my_tasks(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取当前用户在项目中的任务列表。"""
    session = require_login(session_id)
    resp = await api_get(f"/projects/{project_id}/tasks", session_id=session_id)
    members_resp = await api_get(f"/projects/{project_id}/members", session_id=session_id)
    my_member_ids = {
        m["id"] for m in members_resp.get("data", [])
        if m.get("user_id") == session.user_id or m.get("name") == session.display_name
    }
    my_tasks = [t for t in resp.get("data", []) if t.get("owner_id") in my_member_ids]
    return {"success": True, "data": my_tasks}


@register_tool
async def get_today_goals(project_id: str, session_id: str = DEFAULT_SESSION) -> dict:
    """获取今日目标：当前用户的 InProgress/NotStarted 任务，按优先级 + 关键路径排序。"""
    session = require_login(session_id)
    timeline = await api_get(f"/projects/{project_id}/timeline", session_id=session_id)
    data = timeline.get("data", {})
    tasks = data.get("tasks", [])
    members_resp = await api_get(f"/projects/{project_id}/members", session_id=session_id)
    my_member_ids = {
        m["id"] for m in members_resp.get("data", [])
        if m.get("user_id") == session.user_id or m.get("name") == session.display_name
    }

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    my_tasks = [
        t for t in tasks
        if t.get("owner_id") in my_member_ids and t.get("status") in ("InProgress", "NotStarted")
    ]
    my_tasks.sort(key=lambda t: (
        not t.get("is_on_critical_path", False),
        priority_order.get(t.get("priority", "P3"), 9),
    ))
    return {"success": True, "data": my_tasks}


@register_tool
async def update_task_progress(
    task_id: str,
    progress: float,
    actual_duration: float | None = None,
    status: str | None = None,
    comment: str | None = None,
    blocked_reason: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """更新任务进度。progress 范围 0.0~1.0。当 status=Blocked 时可通过 blocked_reason 记录阻塞原因。"""
    require_login(session_id)
    payload: dict = {"progress": progress}
    if actual_duration is not None:
        payload["actual_duration"] = actual_duration
    if status is not None:
        payload["status"] = status
    if comment is not None:
        payload["comment"] = comment
    if blocked_reason is not None:
        payload["blocked_reason"] = blocked_reason
    return await api_post(f"/tasks/{task_id}/progress", json=payload, session_id=session_id)


@register_tool
async def submit_task_completion(
    task_id: str,
    actual_duration: float | None = None,
    comment: str | None = None,
    result_type: str | None = None,
    result_content: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """提交任务完成。自动设置 progress=1.0, status=Completed。可附带 result_type 和 result_content。"""
    require_login(session_id)
    payload: dict = {"progress": 1.0, "status": "Completed"}
    if actual_duration is not None:
        payload["actual_duration"] = actual_duration
    if comment is not None:
        payload["comment"] = comment
    if result_type is not None:
        payload["result_type"] = result_type
    if result_content is not None:
        payload["result_content"] = result_content
    return await api_post(f"/tasks/{task_id}/progress", json=payload, session_id=session_id)


@register_tool
async def add_task_assignee(
    task_id: str,
    member_id: str,
    workload_ratio: float = 1.0,
    role: str | None = None,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """为任务添加协作者。

    workload_ratio 范围 0.0~1.0，表示该成员承担的工作量比例。
    role 为可选的协作角色描述，如"前端开发"、"测试"等。

    注意：
    1. 如果添加协作者后总工作量占比超过 1.0，系统会自动按比例缩减所有协作者（包括新添加的）的占比。
       例如：现有 A (0.5), B (0.5)，添加 C (0.1) 后，总和为 1.1
       系统会自动缩减为：A (0.4545), B (0.4545), C (0.0909)，总和保持 1.0

    2. 如果新协作者的 workload_ratio 高于当前主负责人（owner），
       建议使用 update_task 将 owner_id 更新为该协作者，以保持主负责人为权重最高的成员。
    """
    require_login(session_id)
    payload = {"member_id": member_id, "workload_ratio": workload_ratio}
    if role:
        payload["role"] = role
    return await api_post(f"/tasks/{task_id}/assignees", json=payload, session_id=session_id)


@register_tool
async def remove_task_assignee(
    task_id: str,
    assignee_id: int,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """移除任务协作者。

    assignee_id 为协作者记录的 ID（从任务详情中获取）。

    注意：删除协作者后，系统会自动将被删除协作者的工作量占比按比例重新分配给剩余的协作者。
    例如：如果有 3 个协作者占比分别为 0.5, 0.3, 0.2，删除占比 0.2 的协作者后，
    剩余两个协作者的占比会按比例调整为 0.625 (0.5 + 0.2*0.625) 和 0.375 (0.3 + 0.2*0.375)。
    """
    require_login(session_id)
    return await api_delete(f"/tasks/{task_id}/assignees/{assignee_id}", session_id=session_id)
