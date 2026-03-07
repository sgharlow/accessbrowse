"""Tests for FastAPI WebSocket server."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_app_creates():
    from main import app
    assert app is not None
    assert app.title == "AccessBrowse"


@pytest.mark.asyncio
async def test_health_endpoint():
    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "active_sessions" in data
    assert "max_sessions" in data


def test_app_version():
    from main import app
    assert app.version == "1.0.0"


def test_cors_middleware_configured():
    from main import app
    assert any(
        m.cls.__name__ == "CORSMiddleware" for m in app.user_middleware
    ), "CORSMiddleware should be configured on the app"


@pytest.mark.asyncio
async def test_health_returns_correct_max_sessions():
    import httpx
    from main import app
    from config import MAX_CONCURRENT_SESSIONS

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    data = resp.json()
    assert data["max_sessions"] == MAX_CONCURRENT_SESSIONS


@pytest.mark.asyncio
async def test_health_initial_zero_sessions():
    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    data = resp.json()
    assert data["active_sessions"] == 0
