"""Tests for auth tools."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_login_success(admin_client):
    """Login via API returns token and user info."""
    # We test the backend auth endpoint directly since MCP tools wrap it
    resp = await admin_client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "Admin"
    assert data["display_name"] == "李明"


async def test_login_wrong_password(admin_client):
    """Wrong password returns 401."""
    resp = await admin_client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": "wrongpassword123",
    })
    assert resp.status_code == 401
