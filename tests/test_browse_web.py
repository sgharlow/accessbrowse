# tests/test_browse_web.py
"""Tests for browse_web tool — multi-step action loop."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@pytest.mark.asyncio
async def test_browse_web_returns_string():
    """browse_web should always return a string summary."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    messages = []

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "fakebase64", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    async def fake_send(msg):
        messages.append(msg)
        # Re-set events so the tool doesn't block after clear()
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    # Pre-set events so the tool doesn't block
    screenshot_event.set()
    action_event.set()

    # Mock plan_action to return "done" immediately
    import tools.action_planner as ap
    original = ap.plan_action

    async def mock_plan_action(**kwargs):
        return {"action": "done", "summary": "Found the results"}

    ap.plan_action = mock_plan_action
    # Zero out settle delays for fast tests
    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        result = await browse_web(
            url="https://example.com",
            task="find stuff",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        assert isinstance(result, str)
        assert "Found the results" in result
    finally:
        ap.plan_action = original
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act


@pytest.mark.asyncio
async def test_browse_web_max_steps():
    """browse_web should stop after MAX_BROWSE_STEPS."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web
    from config import MAX_BROWSE_STEPS

    step_count = 0

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "fakebase64", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    async def fake_send(msg):
        # Re-set events so the tool doesn't block after clear()
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    screenshot_event.set()
    action_event.set()

    import tools.action_planner as ap
    original = ap.plan_action

    async def mock_plan_action(**kwargs):
        nonlocal step_count
        step_count += 1
        return {"action": "click", "coordinate": [500, 500]}

    ap.plan_action = mock_plan_action
    # Zero out settle delays for fast tests
    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        result = await browse_web(
            url="https://example.com",
            task="keep clicking",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        assert step_count == MAX_BROWSE_STEPS
        assert "maximum steps" in result.lower() or isinstance(result, str)
    finally:
        ap.plan_action = original
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act


@pytest.mark.asyncio
async def test_browse_web_screenshot_timeout():
    """browse_web should handle screenshot timeout gracefully."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {}
        _action_data = {"success": True}

    async def fake_send(msg):
        if msg.get("type") == "execute_action":
            action_event.set()
        # Don't set screenshot_event — simulate timeout

    action_event.set()

    orig_nav = bw._NAVIGATE_SETTLE
    orig_act = bw._ACTION_SETTLE
    orig_timeout = bw.SCREENSHOT_TIMEOUT
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    bw.SCREENSHOT_TIMEOUT = 0.1
    try:
        result = await browse_web(
            url="https://example.com",
            task="test",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=FakeRef(),
            action_event=action_event,
            action_data_ref=FakeRef(),
        )
        assert "screenshot" in result.lower() or "extension" in result.lower()
    finally:
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act
        bw.SCREENSHOT_TIMEOUT = orig_timeout


@pytest.mark.asyncio
async def test_browse_web_missing_image():
    """browse_web should handle missing image in screenshot data."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"url": "https://example.com"}
        _action_data = {"success": True}

    async def fake_send(msg):
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    screenshot_event.set()
    action_event.set()

    orig_nav = bw._NAVIGATE_SETTLE
    orig_act = bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        result = await browse_web(
            url="https://example.com",
            task="test",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=FakeRef(),
            action_event=action_event,
            action_data_ref=FakeRef(),
        )
        assert "screenshot" in result.lower() or "failed" in result.lower()
    finally:
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act


def test_describe_action_click():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "click", "coordinate": [100, 200]})
    assert "clicking" in desc.lower()


def test_describe_action_type():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "type", "text": "hello"})
    assert "typing" in desc.lower()


def test_describe_action_scroll():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "scroll", "direction": "down"})
    assert "scrolling" in desc.lower()


def test_describe_action_hover():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "hover"})
    assert "hovering" in desc.lower()


def test_describe_action_key():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "key", "key": "Enter"})
    assert "Enter" in desc


def test_describe_action_go_back():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "go_back"})
    assert "going back" in desc.lower()


def test_describe_action_wait():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "wait"})
    assert "waiting" in desc.lower()


def test_describe_action_unknown():
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "custom_thing"})
    assert "custom_thing" in desc


@pytest.mark.asyncio
async def test_browse_web_multiple_steps_before_done():
    """Mock plan_action to return 'click' twice then 'done', verify 2 actions executed."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    step_count = 0
    messages = []

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "fakebase64", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    async def fake_send(msg):
        messages.append(msg)
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    screenshot_event.set()
    action_event.set()

    import tools.action_planner as ap
    original = ap.plan_action

    async def mock_plan_action(**kwargs):
        nonlocal step_count
        step_count += 1
        if step_count <= 2:
            return {"action": "click", "coordinate": [100, 200]}
        return {"action": "done", "summary": "All done after 2 clicks"}

    ap.plan_action = mock_plan_action
    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        result = await browse_web(
            url="https://example.com",
            task="click twice then finish",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        assert step_count == 3  # 2 clicks + 1 done
        execute_actions = [m for m in messages if m.get("type") == "execute_action" and m.get("action") == "click"]
        assert len(execute_actions) == 2
        assert "All done after 2 clicks" in result
    finally:
        ap.plan_action = original
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act


@pytest.mark.asyncio
async def test_browse_web_action_timeout():
    """Mock plan_action to return 'click', set ACTION_TIMEOUT=0.1 and don't set action_event."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "fakebase64", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    call_count = 0

    async def fake_send(msg):
        nonlocal call_count
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            # Don't set action_event for click actions — simulate timeout
            if msg.get("action") == "navigate":
                action_event.set()

    screenshot_event.set()
    action_event.set()

    import tools.action_planner as ap
    original = ap.plan_action

    async def mock_plan_action(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"action": "click", "coordinate": [100, 200]}
        return {"action": "done", "summary": "Done after timeout"}

    ap.plan_action = mock_plan_action
    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    orig_action_timeout = bw.ACTION_TIMEOUT
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    bw.ACTION_TIMEOUT = 0.1
    try:
        result = await browse_web(
            url="https://example.com",
            task="test timeout",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        # Should complete without error despite action timeout
        assert isinstance(result, str)
        assert "Done after timeout" in result
    finally:
        ap.plan_action = original
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act
        bw.ACTION_TIMEOUT = orig_action_timeout


@pytest.mark.asyncio
async def test_browse_web_sends_navigate_first():
    """Verify first message sent includes type='execute_action' and action='navigate'."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    messages = []

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "fakebase64", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    async def fake_send(msg):
        messages.append(msg)
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    screenshot_event.set()
    action_event.set()

    import tools.action_planner as ap
    original = ap.plan_action

    async def mock_plan_action(**kwargs):
        return {"action": "done", "summary": "Immediate done"}

    ap.plan_action = mock_plan_action
    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        await browse_web(
            url="https://example.com",
            task="test navigate",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        # Find the first execute_action message
        execute_msgs = [m for m in messages if m.get("type") == "execute_action"]
        assert len(execute_msgs) >= 1
        first_execute = execute_msgs[0]
        assert first_execute["action"] == "navigate"
        assert first_execute["url"] == "https://example.com"
    finally:
        ap.plan_action = original
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act


def test_describe_action_done():
    """_describe_action({'action': 'done'}) returns 'done'."""
    from tools.browse_web import _describe_action
    desc = _describe_action({"action": "done"})
    assert desc == "done"


def test_describe_action_empty():
    """_describe_action({}) returns empty string."""
    from tools.browse_web import _describe_action
    desc = _describe_action({})
    assert desc == ""


@pytest.mark.asyncio
async def test_browse_web_empty_image_after_navigate():
    """Screenshot has empty 'image': '', verify returns failure message."""
    import tools.browse_web as bw
    from tools.browse_web import browse_web

    screenshot_event = asyncio.Event()
    action_event = asyncio.Event()

    class FakeRef:
        _screenshot_data = {"image": "", "url": "https://example.com", "title": "Example"}
        _action_data = {"success": True}

    ref = FakeRef()

    async def fake_send(msg):
        if msg.get("type") == "request_screenshot":
            screenshot_event.set()
        elif msg.get("type") == "execute_action":
            action_event.set()

    screenshot_event.set()
    action_event.set()

    orig_nav, orig_act = bw._NAVIGATE_SETTLE, bw._ACTION_SETTLE
    bw._NAVIGATE_SETTLE = 0
    bw._ACTION_SETTLE = 0
    try:
        result = await browse_web(
            url="https://example.com",
            task="test empty image",
            send_to_client=fake_send,
            screenshot_event=screenshot_event,
            screenshot_data_ref=ref,
            action_event=action_event,
            action_data_ref=ref,
        )
        assert "failed" in result.lower() or "screenshot" in result.lower()
    finally:
        bw._NAVIGATE_SETTLE = orig_nav
        bw._ACTION_SETTLE = orig_act
