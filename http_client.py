"""Async HTTP client wrapper for calling the TimeLiner backend API."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_server.auth import get_session, DEFAULT_SESSION
from mcp_server.config import BACKEND_BASE_URL, REQUEST_TIMEOUT


def _build_headers(session_id: str = DEFAULT_SESSION) -> dict[str, str]:
    session = get_session(session_id)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if session.token:
        headers["Authorization"] = f"Bearer {session.token}"
    return headers


async def api_get(path: str, *, session_id: str = DEFAULT_SESSION, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(path, headers=_build_headers(session_id), params=params)
        if resp.status_code == 401:
            raise PermissionError("认证失败，请重新登录")
        resp.raise_for_status()
        return resp.json()


async def api_post(path: str, *, session_id: str = DEFAULT_SESSION, json: Any = None, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(path, headers=_build_headers(session_id), json=json, params=params)
        if resp.status_code == 401:
            raise PermissionError("认证失败，请重新登录")
        resp.raise_for_status()
        return resp.json()


async def api_put(path: str, *, session_id: str = DEFAULT_SESSION, json: Any = None) -> Any:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        resp = await client.put(path, headers=_build_headers(session_id), json=json)
        if resp.status_code == 401:
            raise PermissionError("认证失败，请重新登录")
        resp.raise_for_status()
        return resp.json()


async def api_delete(path: str, *, session_id: str = DEFAULT_SESSION) -> Any:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        resp = await client.delete(path, headers=_build_headers(session_id))
        if resp.status_code == 401:
            raise PermissionError("认证失败，请重新登录")
        if resp.status_code == 204:
            return {"success": True}
        resp.raise_for_status()
        return resp.json()
