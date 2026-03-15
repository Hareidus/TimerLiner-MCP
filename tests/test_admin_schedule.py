"""Tests for admin schedule approval tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member

pytestmark = pytest.mark.asyncio


async def _create_schedule_request(client, project_id: str, requester_id: str) -> dict:
    resp = await client.post(
        "/api/schedule/requests",
        params={"project_id": project_id},
        json={"requester_id": requester_id, "reason": "需要延期"},
    )
    assert resp.status_code == 200
    return resp.json()["data"]


async def test_list_schedule_requests(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    await _create_schedule_request(admin_client, project["id"], member["id"])
    resp = await admin_client.get(f"/api/schedule/projects/{project['id']}/requests")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["status"] == "Pending"


async def test_approve_schedule_request(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    sr = await _create_schedule_request(admin_client, project["id"], member["id"])
    resp = await admin_client.post(f"/api/schedule/requests/{sr['id']}/approve", json={
        "approver_id": "user-test-admin",
        "approved_solution": {"action": "延期3天"},
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "Approved"


async def test_reject_schedule_request(admin_client):
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    sr = await _create_schedule_request(admin_client, project["id"], member["id"])
    resp = await admin_client.post(f"/api/schedule/requests/{sr['id']}/reject", json={
        "approver_id": "user-test-admin",
        "reject_reason": "资源不足",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "Rejected"
    assert data["reject_reason"] == "资源不足"
