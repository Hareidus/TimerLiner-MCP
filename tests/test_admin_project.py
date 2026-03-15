"""Tests for admin project management tools."""

import pytest

from mcp_server.tests.conftest import create_test_project

pytestmark = pytest.mark.asyncio


async def test_create_project(admin_client):
    project = await create_test_project(admin_client)
    assert project["id"].startswith("proj-")
    assert project["status"] == "NotStarted"
    assert project["name"] == "测试项目"


async def test_list_projects(admin_client):
    await create_test_project(admin_client)
    await create_test_project(admin_client)
    resp = await admin_client.get("/api/projects")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


async def test_get_project(admin_client):
    project = await create_test_project(admin_client)
    resp = await admin_client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "测试项目"


async def test_update_project(admin_client):
    project = await create_test_project(admin_client)
    resp = await admin_client.put(f"/api/projects/{project['id']}", json={
        "status": "InProgress",
        "progress": 0.5,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "InProgress"
    assert data["progress"] == 0.5


async def test_delete_project(admin_client):
    project = await create_test_project(admin_client)
    resp = await admin_client.delete(f"/api/projects/{project['id']}")
    assert resp.status_code == 200
    resp2 = await admin_client.get(f"/api/projects/{project['id']}")
    assert resp2.status_code == 404


async def test_get_project_dashboard(admin_client):
    project = await create_test_project(admin_client)
    resp = await admin_client.get(f"/api/projects/{project['id']}/timeline")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "summary" in data
    assert "tasks" in data
    assert "members" in data
