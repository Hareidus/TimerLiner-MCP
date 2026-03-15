"""Tests for shared context and query tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member, create_test_task

pytestmark = pytest.mark.asyncio


async def test_get_project_context(admin_client):
    project = await create_test_project(admin_client)
    await create_test_member(admin_client, project["id"])
    await create_test_task(admin_client, project["id"])
    resp = await admin_client.get(f"/api/context/project/{project['id']}")
    assert resp.status_code == 200
    md = resp.json()["data"]
    assert "# 项目信息" in md


async def test_get_task_context(admin_client):
    project = await create_test_project(admin_client)
    task = await create_test_task(admin_client, project["id"])
    resp = await admin_client.get(f"/api/context/task/{task['id']}")
    assert resp.status_code == 200
    md = resp.json()["data"]
    assert "## 依赖关系" in md


async def test_get_project_activities(admin_client):
    project = await create_test_project(admin_client)
    resp = await admin_client.get(f"/api/projects/{project['id']}/activities")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data
