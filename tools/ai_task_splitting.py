"""AI task splitting MCP tools: ai_split_task, confirm_and_distribute_tasks."""

from __future__ import annotations

import json
from typing import Any

from mcp_server.tool_registry import register_tool
from mcp_server.auth import require_project_manager, DEFAULT_SESSION
from mcp_server.http_client import api_get, api_post
from mcp_server.prompts.task_splitting import build_task_splitting_prompt


@register_tool
async def ai_split_task(
    project_id: str,
    task_description: str,
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """AI 拆分任务：输入任务描述 → 获取项目上下文 → 生成子任务方案 → 返回待确认计划。

    返回的 task_plan 可直接传给 confirm_and_distribute_tasks 进行批量创建。
    """
    await require_project_manager(session_id, project_id)

    # 1. 获取项目上下文
    ctx_resp = await api_get(f"/context/project/{project_id}", session_id=session_id)
    project_context_md = ctx_resp.get("data", "")

    # 2. 构造 prompt
    prompt = build_task_splitting_prompt(
        task_description=task_description,
        project_context_md=project_context_md,
    )

    # 3. 返回 prompt 和上下文，让调用方（LLM client）执行拆分
    # MCP Server 本身不直接调用 LLM，而是返回结构化的 prompt 供 MCP client 侧的 LLM 处理
    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "task_description": task_description,
            "prompt": prompt,
            "project_context": project_context_md,
            "instructions": (
                "请使用此 prompt 调用 LLM 获取子任务方案（JSON 数组），"
                "然后调用 confirm_and_distribute_tasks 传入 project_id 和 task_plan 完成分发。"
            ),
        },
    }


@register_tool
async def confirm_and_distribute_tasks(
    project_id: str,
    task_plan: list[dict[str, Any]],
    session_id: str = DEFAULT_SESSION,
) -> dict:
    """批量确认并分发 AI 拆分的任务方案。

    task_plan 格式: [{name, description, priority, estimated_duration, suggested_owner_id, dependencies}]
    dependencies 为子任务索引数组（从 0 开始），表示当前任务依赖哪些前置任务。
    """
    await require_project_manager(session_id, project_id)

    created_tasks: list[dict] = []
    index_to_task_id: dict[int, str] = {}

    # 1. 按顺序创建任务
    for idx, item in enumerate(task_plan):
        payload: dict = {
            "name": item["name"],
            "estimated_duration": item["estimated_duration"],
            "priority": item.get("priority", "P2"),
        }
        if item.get("description"):
            payload["description"] = item["description"]
        if item.get("suggested_owner_id"):
            payload["owner_id"] = item["suggested_owner_id"]
        if item.get("deadline"):
            payload["deadline"] = item["deadline"]

        resp = await api_post(f"/projects/{project_id}/tasks", json=payload, session_id=session_id)
        task_data = resp.get("data", {})
        task_id = task_data.get("id", "")
        index_to_task_id[idx] = task_id
        created_tasks.append(task_data)

    # 2. 设置依赖关系
    dependency_results: list[dict] = []
    for idx, item in enumerate(task_plan):
        deps = item.get("dependencies", [])
        successor_id = index_to_task_id.get(idx)
        if not successor_id:
            continue
        for dep_idx in deps:
            predecessor_id = index_to_task_id.get(dep_idx)
            if not predecessor_id:
                continue
            try:
                dep_resp = await api_post(
                    f"/tasks/{successor_id}/dependencies",
                    json={"predecessor_task_id": predecessor_id},
                    session_id=session_id,
                )
                dependency_results.append(dep_resp.get("data", {}))
            except Exception as e:
                dependency_results.append({"error": str(e), "successor": successor_id, "predecessor": predecessor_id})

    # 3. 验证整体方案
    changes: list[dict] = []
    for idx, item in enumerate(task_plan):
        task_id = index_to_task_id.get(idx)
        if not task_id:
            continue
        change: dict = {"task_id": task_id}
        if item.get("suggested_owner_id"):
            change["owner_id"] = item["suggested_owner_id"]
        change["estimated_duration"] = item["estimated_duration"]
        if item.get("priority"):
            change["priority"] = item["priority"]
        changes.append(change)

    validation: dict = {}
    try:
        validation = await api_post(
            "/decision/validate",
            json={"project_id": project_id, "decision_type": "task_distribution", "changes": changes},
            session_id=session_id,
        )
    except Exception as e:
        validation = {"error": str(e)}

    # 4. 如果验证通过，应用决策
    applied: dict = {}
    if validation.get("data", {}).get("valid", False):
        try:
            applied = await api_post(
                "/decision/apply",
                json={"project_id": project_id, "decision_type": "task_distribution", "changes": changes},
                session_id=session_id,
            )
        except Exception as e:
            applied = {"error": str(e)}

    return {
        "success": True,
        "data": {
            "created_tasks": created_tasks,
            "task_count": len(created_tasks),
            "dependencies": dependency_results,
            "validation": validation,
            "applied": applied,
        },
    }
