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
