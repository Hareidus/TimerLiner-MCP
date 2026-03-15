"""Tests for admin task management tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member, create_test_task

pytestmark = pytest.mark.asyncio


async def test_create_task(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    assert task["id"].startswith("task-")
    assert task["priority"] == "P1"
    assert task["status"] == "NotStarted"


async def test_list_tasks(admin_client):
    project = await create_test_project(admin_client)
    await create_test_task(admin_client, project["id"], name="任务A")
    await create_test_task(admin_client, project["id"], name="任务B")
    await create_test_task(admin_client, project["id"], name="任务C")
    resp = await admin_client.get(f"/api/projects/{project['id']}/tasks")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 3


async def test_get_task(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.get(f"/api/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "测试任务"


async def test_update_task(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.put(f"/api/tasks/{task['id']}", json={"status": "InProgress"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "InProgress"


async def test_delete_task(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.delete(f"/api/tasks/{task['id']}")
    assert resp.status_code == 200
    resp2 = await admin_client.get(f"/api/tasks/{task['id']}")
    assert resp2.status_code == 404


async def test_add_task_dependency(admin_client):
    project = await create_test_project(admin_client)
    task_a = await create_test_task(admin_client, project["id"], name="A")
    task_b = await create_test_task(admin_client, project["id"], name="B")
    resp = await admin_client.post(f"/api/tasks/{task_b['id']}/dependencies", json={
        "predecessor_task_id": task_a["id"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["predecessor_task_id"] == task_a["id"]
    assert data["successor_task_id"] == task_b["id"]


async def test_ai_split_task_mock(admin_client):
    """Test that project context endpoint returns markdown for AI splitting."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    await create_test_task(admin_client, project["id"], owner_id=member["id"])
    resp = await admin_client.get(f"/api/context/project/{project['id']}")
    assert resp.status_code == 200
    md = resp.json()["data"]
    assert "# 项目信息" in md
    assert "## 任务列表" in md
    assert "## 成员列表" in md


async def test_confirm_and_distribute_tasks(admin_client):
    """Test batch task creation + dependency setup."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])

    # Create 3 tasks with dependencies: B depends on A, C depends on B
    task_a = await create_test_task(admin_client, project["id"], name="A", owner_id=member["id"])
    task_b = await create_test_task(admin_client, project["id"], name="B", owner_id=member["id"])
    task_c = await create_test_task(admin_client, project["id"], name="C", owner_id=member["id"])

    # Set dependencies
    resp1 = await admin_client.post(f"/api/tasks/{task_b['id']}/dependencies", json={
        "predecessor_task_id": task_a["id"],
    })
    assert resp1.status_code == 200

    resp2 = await admin_client.post(f"/api/tasks/{task_c['id']}/dependencies", json={
        "predecessor_task_id": task_b["id"],
    })
    assert resp2.status_code == 200

    # Verify all tasks exist
    resp = await admin_client.get(f"/api/projects/{project['id']}/tasks")
    assert len(resp.json()["data"]) == 3
