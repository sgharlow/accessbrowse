# tests/test_read_page.py
"""Tests for read_page tool — accessibility page summaries."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_read_prompt_has_required_sections():
    from tools.read_page import READ_PROMPT
    assert "Page Identity" in READ_PROMPT
    assert "Key Content" in READ_PROMPT
    assert "Available Actions" in READ_PROMPT
    assert "{focus}" in READ_PROMPT


@pytest.mark.asyncio
async def test_read_page_no_extension():
    """read_page should return error message when no extension connected."""
    from tools.read_page import read_page
    result = await read_page(
        focus="main content",
        send_to_client=None,
        screenshot_event=None,
        screenshot_data_ref=None,
    )
    assert "extension" in result.lower() or "connection" in result.lower()


@pytest.mark.asyncio
async def test_read_page_screenshot_timeout():
    """read_page should handle screenshot timeout gracefully."""
    from tools.read_page import read_page

    async def fake_send(msg):
        pass

    screenshot_event = asyncio.Event()
    # Don't set the event — simulates timeout

    class FakeRef:
        _screenshot_data = {}

    result = await read_page(
        focus="main content",
        send_to_client=fake_send,
        screenshot_event=screenshot_event,
        screenshot_data_ref=FakeRef(),
        timeout=0.1,  # Very short timeout for test
    )
    assert "couldn't" in result.lower() or "try again" in result.lower()
