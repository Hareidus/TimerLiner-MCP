"""Tests for admin member management tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member

pytestmark = pytest.mark.asyncio


async def test_add_member(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    assert member["id"].startswith("mem-")
    assert member["name"] == "张三"


async def test_list_members(admin_client):
    project = await create_test_project(admin_client)
    await create_test_member(admin_client, project["id"], name="张三")
    await create_test_member(admin_client, project["id"], name="李四")
    resp = await admin_client.get(f"/api/projects/{project['id']}/members")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


async def test_get_member(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.get(f"/api/members/{member['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "张三"


async def test_update_member(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.put(f"/api/members/{member['id']}", json={
        "availability_status": "Busy",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["default_availability_status"] == "Busy"


async def test_remove_member(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.delete(f"/api/members/{member['id']}")
    assert resp.status_code == 200
    resp2 = await admin_client.get(f"/api/members/{member['id']}")
    assert resp2.status_code == 404


async def test_add_member_skill(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.post(f"/api/members/{member['id']}/skills", json={
        "skill_name": "Python",
        "skill_description": "后端开发",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["skill_name"] == "Python"


async def test_list_member_skills(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    await admin_client.post(f"/api/members/{member['id']}/skills", json={"skill_name": "Python"})
    await admin_client.post(f"/api/members/{member['id']}/skills", json={"skill_name": "FastAPI"})
    resp = await admin_client.get(f"/api/members/{member['id']}/skills")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


async def test_remove_member_skill(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    skill_resp = await admin_client.post(f"/api/members/{member['id']}/skills", json={"skill_name": "Python"})
    skill_id = skill_resp.json()["data"]["id"]
    resp = await admin_client.delete(f"/api/members/{member['id']}/skills/{skill_id}")
    assert resp.status_code == 200
    resp2 = await admin_client.get(f"/api/members/{member['id']}/skills")
    assert len(resp2.json()["data"]) == 0
