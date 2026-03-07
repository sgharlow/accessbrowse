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


@pytest.mark.asyncio
async def test_health_status_field():
    """Health endpoint returns status = 'ok'."""
    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_websocket_accepts_connection():
    """WebSocket endpoint at /ws accepts a connection."""
    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="ws://testserver",
        ) as ws_client:
            # Use the starlette test client approach for WebSocket
            from starlette.testclient import TestClient
            test_client = TestClient(app)
            with test_client.websocket_connect("/ws") as websocket:
                # If we reach here, connection was accepted
                assert websocket is not None


def test_app_has_websocket_route():
    """Verify /ws route exists in app.routes."""
    from main import app

    ws_paths = [
        r.path for r in app.routes if hasattr(r, "path") and r.path == "/ws"
    ]
    assert "/ws" in ws_paths, "/ws route should exist in app routes"


@pytest.mark.asyncio
async def test_health_response_keys():
    """Health endpoint returns exactly 3 keys: status, active_sessions, max_sessions."""
    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    data = resp.json()
    assert set(data.keys()) == {"status", "active_sessions", "max_sessions"}


def test_app_has_health_route():
    """Verify /health route exists in app.routes."""
    from main import app

    health_paths = [
        r.path for r in app.routes if hasattr(r, "path") and r.path == "/health"
    ]
    assert "/health" in health_paths, "/health route should exist in app routes"


def test_sessions_manager_initialized():
    """Verify sessions module-level object exists and is a SessionManager."""
    from main import sessions
    from services.session_manager import SessionManager

    assert isinstance(sessions, SessionManager)
