"""Tests for admin milestone management tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_task

pytestmark = pytest.mark.asyncio


async def test_create_milestone(admin_client):
    project = await create_test_project(admin_client)
    t1 = await create_test_task(admin_client, project["id"], name="T1")
    t2 = await create_test_task(admin_client, project["id"], name="T2")
    resp = await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "里程碑1",
        "target_date": "2026-03-01T00:00:00Z",
        "task_ids": [t1["id"], t2["id"]],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"].startswith("ms-")
    assert data["completion_rate"] == 0.0


async def test_list_milestones(admin_client):
    project = await create_test_project(admin_client)
    await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "M1",
        "target_date": "2026-03-01T00:00:00Z",
        "task_ids": [],
    })
    resp = await admin_client.get(f"/api/projects/{project['id']}/milestones")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


async def test_get_milestone(admin_client):
    project = await create_test_project(admin_client)
    t1 = await create_test_task(admin_client, project["id"], name="T1")
    ms_resp = await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "M1",
        "target_date": "2026-03-01T00:00:00Z",
        "task_ids": [t1["id"]],
    })
    ms_id = ms_resp.json()["data"]["id"]
    resp = await admin_client.get(f"/api/milestones/{ms_id}")
    assert resp.status_code == 200
    assert t1["id"] in resp.json()["data"]["task_ids"]


async def test_update_milestone(admin_client):
    project = await create_test_project(admin_client)
    ms_resp = await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "M1",
        "target_date": "2026-03-01T00:00:00Z",
        "task_ids": [],
    })
    ms_id = ms_resp.json()["data"]["id"]
    resp = await admin_client.put(f"/api/milestones/{ms_id}", json={
        "target_date": "2026-04-01T00:00:00Z",
    })
    assert resp.status_code == 200
    assert "2026-04-01" in resp.json()["data"]["target_date"]


async def test_delete_milestone(admin_client):
    project = await create_test_project(admin_client)
    ms_resp = await admin_client.post(f"/api/projects/{project['id']}/milestones", json={
        "name": "M1",
        "target_date": "2026-03-01T00:00:00Z",
        "task_ids": [],
    })
    ms_id = ms_resp.json()["data"]["id"]
    resp = await admin_client.delete(f"/api/milestones/{ms_id}")
    assert resp.status_code == 200
    resp2 = await admin_client.get(f"/api/milestones/{ms_id}")
    assert resp2.status_code == 404
