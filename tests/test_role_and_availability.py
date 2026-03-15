"""Tests for MCP tool reorganization — project role permissions and availability patterns.

Tests the new resource-based tool files with require_project_manager / require_self_or_manager.
"""

from datetime import UTC, datetime, timedelta

import pytest

from mcp_server.tests.conftest import (
    ADMIN_USER,
    NORMAL_USER,
    create_test_project,
    create_test_member,
    create_test_task,
)

pytestmark = pytest.mark.asyncio


# ============================================================
# Project Role in Member Responses
# ============================================================

async def test_member_has_project_role_field(admin_client):
    """成员响应包含 project_role 字段。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.get(f"/api/members/{member['id']}")
    assert resp.status_code == 200
    assert "project_role" in resp.json()["data"]
    assert resp.json()["data"]["project_role"] == "Member"


async def test_project_creator_auto_owner(admin_client):
    """项目创建者自动成为 Owner。"""
    project = await create_test_project(admin_client)
    resp = await admin_client.get(f"/api/projects/{project['id']}/members")
    assert resp.status_code == 200
    members = resp.json()["data"]
    owners = [m for m in members if m.get("project_role") == "Owner"]
    assert len(owners) >= 1


# ============================================================
# Permission: Normal User vs Owner/Admin
# ============================================================

async def test_normal_user_cannot_create_task(admin_client, user_client):
    """普通用户不能创建任务（需要 Owner/Admin）。"""
    project = await create_test_project(admin_client)
    resp = await user_client.post(f"/api/projects/{project['id']}/tasks", json={
        "name": "非法任务",
        "estimated_duration": 4,
        "priority": "P2",
    })
    assert resp.status_code == 403


async def test_normal_user_cannot_create_milestone(admin_client, user_client):
    """普通用户不能创建里程碑。"""
    project = await create_test_project(admin_client)
    resp = await user_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "非法里程碑",
        "target_date": "2026-06-01T00:00:00Z",
    })
    assert resp.status_code == 403


async def test_normal_user_cannot_delete_member(admin_client, user_client):
    """普通用户不能删除成员。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await user_client.delete(f"/api/members/{member['id']}")
    assert resp.status_code == 403


async def test_admin_can_do_everything(admin_client):
    """Admin 可以执行所有管理操作。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"], name="测试A")
    task = await create_test_task(admin_client, project["id"], owner_id=member["id"])

    # 创建里程碑
    ms_resp = await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "里程碑A",
        "target_date": "2026-06-01T00:00:00Z",
        "task_ids": [task["id"]],
    })
    assert ms_resp.status_code == 200

    # 删除任务
    del_resp = await admin_client.delete(f"/api/tasks/{task['id']}")
    assert del_resp.status_code == 200


# ============================================================
# Availability Overrides (renamed endpoints)
# ============================================================

async def test_override_crud_via_new_endpoint(admin_client):
    """通过新的 /availability-overrides 端点进行 CRUD。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"], name="覆盖测试")

    now = datetime.now(UTC)

    # Create
    resp = await admin_client.post(
        f"/api/members/{member['id']}/availability-overrides",
        json={
            "start_time": (now + timedelta(hours=2)).isoformat(),
            "end_time": (now + timedelta(hours=4)).isoformat(),
            "status": "Busy",
            "reason": "会议",
        },
    )
    assert resp.status_code == 200
    oid = resp.json()["data"]["id"]

    # List
    list_resp = await admin_client.get(f"/api/members/{member['id']}/availability-overrides")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1

    # Delete
    del_resp = await admin_client.delete(f"/api/members/{member['id']}/availability-overrides/{oid}")
    assert del_resp.status_code == 200


# ============================================================
# Availability Patterns (new feature)
# ============================================================

async def test_pattern_crud(admin_client):
    """周期性可用时间模式 CRUD。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"], name="模式测试")

    # Create
    resp = await admin_client.post(
        f"/api/members/{member['id']}/availability-patterns",
        json={
            "day_of_week": 0,
            "start_time": "09:00",
            "end_time": "18:00",
            "timezone": "Asia/Shanghai",
            "status": "Available",
        },
    )
    assert resp.status_code == 200
    pid = resp.json()["data"]["id"]
    assert resp.json()["data"]["day_of_week"] == 0

    # List
    list_resp = await admin_client.get(f"/api/members/{member['id']}/availability-patterns")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1

    # Update
    upd_resp = await admin_client.put(
        f"/api/members/{member['id']}/availability-patterns/{pid}",
        json={"end_time": "20:00"},
    )
    assert upd_resp.status_code == 200

    # Delete
    del_resp = await admin_client.delete(f"/api/members/{member['id']}/availability-patterns/{pid}")
    assert del_resp.status_code == 200


async def test_pattern_invalid_day(admin_client):
    """day_of_week 超出范围应返回 422。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"], name="验证测试")

    resp = await admin_client.post(
        f"/api/members/{member['id']}/availability-patterns",
        json={
            "day_of_week": 8,
            "start_time": "09:00",
            "end_time": "18:00",
            "status": "Available",
        },
    )
    assert resp.status_code == 422


# ============================================================
# Schedule Request — Owner can approve
# ============================================================

async def test_schedule_request_flow(admin_client):
    """调度申请完整流程：创建 → 列表 → 审批。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])

    # 创建调度申请
    req_resp = await admin_client.post(
        "/api/schedule/requests",
        params={"project_id": project["id"]},
        json={"requester_id": member["id"], "reason": "需要延期"},
    )
    assert req_resp.status_code == 200
    request_id = req_resp.json()["data"]["id"]

    # 列表
    list_resp = await admin_client.get(f"/api/schedule/projects/{project['id']}/requests")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 审批
    approve_resp = await admin_client.post(
        f"/api/schedule/requests/{request_id}/approve",
        json={"approver_id": ADMIN_USER.id},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["data"]["status"] == "Approved"


async def test_normal_user_cannot_approve_schedule(admin_client, user_client):
    """普通用户不能审批调度申请。"""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])

    req_resp = await admin_client.post(
        "/api/schedule/requests",
        params={"project_id": project["id"]},
        json={"requester_id": member["id"], "reason": "测试"},
    )
    assert req_resp.status_code == 200
    request_id = req_resp.json()["data"]["id"]

    approve_resp = await user_client.post(
        f"/api/schedule/requests/{request_id}/approve",
        json={"approver_id": NORMAL_USER.id},
    )
    assert approve_resp.status_code == 403
