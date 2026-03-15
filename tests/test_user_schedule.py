"""Tests for user schedule request tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member

pytestmark = pytest.mark.asyncio


async def test_request_schedule_change(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    resp = await admin_client.post(
        "/api/schedule/requests",
        params={"project_id": project["id"]},
        json={"requester_id": member["id"], "reason": "需要延期一周"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "Pending"
    assert data["reason"] == "需要延期一周"


async def test_get_my_schedule_requests(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    await admin_client.post(
        "/api/schedule/requests",
        params={"project_id": project["id"]},
        json={"requester_id": member["id"], "reason": "延期"},
    )
    resp = await admin_client.get(f"/api/schedule/projects/{project['id']}/requests")
    assert resp.status_code == 200
    data = resp.json()["data"]
    my_requests = [r for r in data if r["requester_id"] == member["id"]]
    assert len(my_requests) == 1
