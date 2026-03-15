"""Test fixtures for MCP Server tests.

Reuses the backend test infrastructure: SQLite in-memory DB, dependency overrides,
and provides admin_client / user_client fixtures.
"""

import os
import sys
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from backend.db.database import Base, get_db
from backend.eventbus.event_bus import Event, event_bus
from backend.main import app
from backend.middleware.auth import get_current_user
from backend.models.user import User


_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

ADMIN_USER = User(
    id="user-test-admin",
    username="li.ming.pm",
    email="admin@test.com",
    password_hash="not-used",
    display_name="李明",
    role="Admin",
    created_at=_NOW,
    updated_at=_NOW,
)

NORMAL_USER = User(
    id="user-test-normal",
    username="chen.yan.dev",
    email="user@test.com",
    password_hash="not-used",
    display_name="陈燕",
    role="User",
    created_at=_NOW,
    updated_at=_NOW,
)


@pytest.fixture()
def _current_user_holder():
    """Mutable holder so we can switch the current user mid-test."""
    return {"user": ADMIN_USER}


@pytest.fixture()
def test_app(tmp_path, monkeypatch, _current_user_holder):
    import backend.models  # noqa: F401

    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user() -> User:
        return _current_user_holder["user"]

    async def publish_noop(_event) -> None:
        return None

    monkeypatch.setattr(event_bus, "publish", publish_noop)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture()
async def admin_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture()
async def user_client(test_app, _current_user_holder) -> AsyncGenerator[AsyncClient, None]:
    _current_user_holder["user"] = NORMAL_USER
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    _current_user_holder["user"] = ADMIN_USER


@pytest.fixture()
def event_collector(monkeypatch):
    """Collect EventBus events for assertions."""
    events: list[Event] = []

    async def capture_publish(evt: Event) -> None:
        events.append(evt)

    monkeypatch.setattr(event_bus, "publish", capture_publish)
    return events


# ── Helper functions ──

async def create_test_project(client: AsyncClient) -> dict:
    resp = await client.post("/api/projects", json={
        "name": "测试项目",
        "description": "测试用",
        "start_time": "2026-01-01T00:00:00Z",
        "deadline": "2026-06-01T00:00:00Z",
    })
    assert resp.status_code == 200
    return resp.json()["data"]


async def create_test_member(client: AsyncClient, project_id: str, name: str = "张三") -> dict:
    resp = await client.post(f"/api/projects/{project_id}/members", json={
        "name": name,
        "contact": f"{name}@test.com",
        "responsibility": "开发",
        "max_workload": 40.0,
        "availability_status": "Available",
    })
    assert resp.status_code == 200
    return resp.json()["data"]


async def create_test_task(
    client: AsyncClient,
    project_id: str,
    name: str = "测试任务",
    estimated_duration: float = 8.0,
    priority: str = "P1",
    owner_id: str | None = None,
) -> dict:
    payload: dict = {
        "name": name,
        "estimated_duration": estimated_duration,
        "priority": priority,
    }
    if owner_id:
        payload["owner_id"] = owner_id
    resp = await client.post(f"/api/projects/{project_id}/tasks", json=payload)
    assert resp.status_code == 200
    return resp.json()["data"]
