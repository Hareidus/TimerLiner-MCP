"""Tests for user task and progress tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member, create_test_task

pytestmark = pytest.mark.asyncio


async def test_get_my_tasks(admin_client):
    """Tasks filtered by owner_id."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"], name="我")
    await create_test_task(admin_client, project["id"], name="我的任务", owner_id=member["id"])
    await create_test_task(admin_client, project["id"], name="别人的任务")
    resp = await admin_client.get(f"/api/projects/{project['id']}/tasks")
    assert resp.status_code == 200
    all_tasks = resp.json()["data"]
    my_tasks = [t for t in all_tasks if t["owner_id"] == member["id"]]
    assert len(my_tasks) == 1
    assert my_tasks[0]["name"] == "我的任务"


async def test_get_today_goals(admin_client):
    """InProgress/NotStarted tasks sorted by priority."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    await create_test_task(admin_client, project["id"], name="P0任务", priority="P0", owner_id=member["id"])
    await create_test_task(admin_client, project["id"], name="P2任务", priority="P2", owner_id=member["id"])
    resp = await admin_client.get(f"/api/projects/{project['id']}/timeline")
    assert resp.status_code == 200
    tasks = resp.json()["data"]["tasks"]
    my_tasks = [t for t in tasks if t["owner_id"] == member["id"] and t["status"] in ("InProgress", "NotStarted")]
    assert len(my_tasks) == 2


async def test_update_task_progress(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.post(f"/api/tasks/{task['id']}/progress", json={
        "progress": 0.6,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["task_progress"] == 0.6


async def test_submit_task_completion(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.post(f"/api/tasks/{task['id']}/progress", json={
        "progress": 1.0,
        "status": "Completed",
    })
    assert resp.status_code == 200
    # Verify task is completed
    resp2 = await admin_client.get(f"/api/tasks/{task['id']}")
    assert resp2.json()["data"]["status"] == "Completed"
    assert resp2.json()["data"]["progress"] == 1.0
