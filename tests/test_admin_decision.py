"""Tests for admin decision tools."""

import pytest

from mcp_server.tests.conftest import create_test_project, create_test_member, create_test_task

pytestmark = pytest.mark.asyncio


async def test_validate_decision_overload(admin_client):
    """Member with max_workload=4, assigning 12h task → valid=false, Overload."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    # Update member max_workload to 4
    await admin_client.put(f"/api/members/{member['id']}", json={"max_workload": 4.0})
    task = await create_test_task(admin_client, project["id"], estimated_duration=2.0, owner_id=member["id"])

    resp = await admin_client.post("/api/decision/validate", json={
        "project_id": project["id"],
        "decision_type": "assignment",
        "changes": [
            {"task_id": task["id"], "owner_id": member["id"], "estimated_duration": 12.0},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is False
    assert any(v["type"] == "Overload" for v in data["violations"])


async def test_apply_decision_success(admin_client):
    """Reasonable assignment → valid=true → apply succeeds."""
    project = await create_test_project(admin_client)
    member = await create_test_member(admin_client, project["id"])
    task = await create_test_task(admin_client, project["id"], estimated_duration=4.0, owner_id=member["id"])

    resp = await admin_client.post("/api/decision/apply", json={
        "project_id": project["id"],
        "decision_type": "assignment",
        "changes": [
            {"task_id": task["id"], "owner_id": member["id"], "estimated_duration": 4.0},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["applied"] is True
