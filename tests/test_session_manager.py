"""Tests for session manager — concurrency control and idle cleanup."""
import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class FakeAgent:
    """Minimal agent stub for testing session manager."""
    def __init__(self):
        self._last_activity = time.monotonic()
        self.closed = False

    @property
    def idle_seconds(self):
        return time.monotonic() - self._last_activity

    def touch(self):
        self._last_activity = time.monotonic()

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_add_and_get_session():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agent = FakeAgent()
    sm.add("sid1", "sess1", agent)
    result = sm.get_by_sid("sid1")
    assert result is not None
    assert result["session_id"] == "sess1"
    assert result["agent"] is agent
    assert sm.active_count == 1


@pytest.mark.asyncio
async def test_max_sessions_enforced():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=2)
    sm.add("sid1", "s1", FakeAgent())
    sm.add("sid2", "s2", FakeAgent())
    assert sm.active_count == 2
    assert sm.at_capacity is True


@pytest.mark.asyncio
async def test_cleanup_removes_session():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agent = FakeAgent()
    sm.add("sid1", "s1", agent)
    await sm.cleanup("sid1")
    assert sm.active_count == 0
    assert sm.get_by_sid("sid1") is None
    assert agent.closed is True


@pytest.mark.asyncio
async def test_cleanup_nonexistent_sid():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    await sm.cleanup("nonexistent")  # Should not raise


@pytest.mark.asyncio
async def test_cleanup_all():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agents = [FakeAgent() for _ in range(3)]
    for i, agent in enumerate(agents):
        sm.add(f"sid{i}", f"s{i}", agent)
    await sm.cleanup_all()
    assert sm.active_count == 0
    assert all(a.closed for a in agents)


@pytest.mark.asyncio
async def test_get_by_sid_nonexistent():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    assert sm.get_by_sid("unknown") is None


@pytest.mark.asyncio
async def test_add_multiple_sessions():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=5)
    agents = [FakeAgent() for _ in range(3)]
    for i, agent in enumerate(agents):
        sm.add(f"sid{i}", f"s{i}", agent)
    assert sm.active_count == 3
    for i in range(3):
        result = sm.get_by_sid(f"sid{i}")
        assert result is not None
        assert result["session_id"] == f"s{i}"
        assert result["agent"] is agents[i]


@pytest.mark.asyncio
async def test_cleanup_closes_agent():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agent = FakeAgent()
    sm.add("sid1", "s1", agent)
    await sm.cleanup("sid1")
    assert agent.closed is True


@pytest.mark.asyncio
async def test_at_capacity_after_cleanup():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=1)
    agent = FakeAgent()
    sm.add("sid1", "s1", agent)
    assert sm.at_capacity is True
    await sm.cleanup("sid1")
    assert sm.at_capacity is False


@pytest.mark.asyncio
async def test_cleanup_all_with_cleanup_task():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    sm.add("sid1", "s1", FakeAgent())
    sm.start_cleanup_loop()
    await sm.cleanup_all()
    assert sm._cleanup_task.done()
    assert sm.active_count == 0


@pytest.mark.asyncio
async def test_session_stores_created_at():
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agent = FakeAgent()
    sm.add("sid1", "s1", agent)
    result = sm.get_by_sid("sid1")
    assert "created_at" in result
    assert isinstance(result["created_at"], float)


@pytest.mark.asyncio
async def test_cleanup_nonexistent_sid_preserves_existing():
    """Cleanup of nonexistent sid should not raise and should preserve existing sessions."""
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=5)
    sm.add("sid1", "s1", FakeAgent())
    sm.add("sid2", "s2", FakeAgent())
    await sm.cleanup("nonexistent")  # Should not raise
    assert sm.active_count == 2
    assert sm.get_by_sid("sid1") is not None
    assert sm.get_by_sid("sid2") is not None


@pytest.mark.asyncio
async def test_start_cleanup_loop_idempotent():
    """Calling start_cleanup_loop() twice doesn't create duplicate tasks."""
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    sm.start_cleanup_loop()
    first_task = sm._cleanup_task
    assert first_task is not None
    sm.start_cleanup_loop()
    second_task = sm._cleanup_task
    assert first_task is second_task
    # Cleanup
    first_task.cancel()
    try:
        await first_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_active_count_after_cleanup():
    """Add 2 sessions, cleanup 1, verify active_count is 1."""
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=5)
    agent1 = FakeAgent()
    agent2 = FakeAgent()
    sm.add("sid1", "s1", agent1)
    sm.add("sid2", "s2", agent2)
    assert sm.active_count == 2
    await sm.cleanup("sid1")
    assert sm.active_count == 1
    assert sm.get_by_sid("sid2") is not None
    assert agent1.closed is True
    assert agent2.closed is False


@pytest.mark.asyncio
async def test_session_data_has_session_id():
    """Add a session, verify the stored dict has 'session_id' key."""
    from services.session_manager import SessionManager
    sm = SessionManager(max_sessions=3)
    agent = FakeAgent()
    sm.add("sid1", "my-session-123", agent)
    result = sm.get_by_sid("sid1")
    assert "session_id" in result
    assert result["session_id"] == "my-session-123"
