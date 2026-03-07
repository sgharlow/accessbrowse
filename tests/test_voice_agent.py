"""Tests for VoiceAgent — GenAI SDK bidi-streaming wrapper."""
import asyncio
import os
import sys
import base64

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class FakeSendFn:
    """Captures messages sent to the client."""
    def __init__(self):
        self.messages = []

    async def __call__(self, msg: dict):
        self.messages.append(msg)


@pytest.mark.asyncio
async def test_voice_agent_init():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    assert agent._screenshot_event is not None
    assert agent._action_event is not None
    assert isinstance(agent._screenshot_event, asyncio.Event)
    assert isinstance(agent._action_event, asyncio.Event)


@pytest.mark.asyncio
async def test_on_screenshot_sets_event():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    assert not agent._screenshot_event.is_set()
    agent.on_screenshot({"image": "abc123", "url": "https://example.com", "title": "Example"})
    assert agent._screenshot_event.is_set()
    assert agent._screenshot_data["image"] == "abc123"


@pytest.mark.asyncio
async def test_on_action_result_sets_event():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    assert not agent._action_event.is_set()
    agent.on_action_result({"success": True})
    assert agent._action_event.is_set()
    assert agent._action_data["success"] is True


@pytest.mark.asyncio
async def test_idle_seconds():
    from agents.voice_agent import VoiceAgent
    import time
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    # idle_seconds should be very small right after creation
    assert agent.idle_seconds < 1.0
    # After touching, it resets
    await asyncio.sleep(0.1)
    agent.touch()
    assert agent.idle_seconds < 0.05


@pytest.mark.asyncio
async def test_silence_frame_is_valid_pcm():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    # 100ms of silence at 16kHz, 16-bit mono = 3200 bytes
    silence_bytes = base64.b64decode(agent._silence_b64)
    assert len(silence_bytes) == 3200
    assert silence_bytes == b"\x00" * 3200


@pytest.mark.asyncio
async def test_voice_agent_closed_flag_default():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    assert agent._closed is False


@pytest.mark.asyncio
async def test_voice_agent_send_audio_when_closed():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    agent._closed = True
    await agent.send_audio("dGVzdA==")
    assert len(send_fn.messages) == 0


@pytest.mark.asyncio
async def test_voice_agent_send_text_when_closed():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    agent._closed = True
    await agent.send_text("hello")
    assert len(send_fn.messages) == 0


@pytest.mark.asyncio
async def test_voice_agent_send_audio_no_live_session():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    # agent._live is None by default; guard should exit early
    await agent.send_audio("dGVzdA==")
    assert len(send_fn.messages) == 0


@pytest.mark.asyncio
async def test_voice_agent_send_text_no_live_session():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    # agent._live is None by default; guard should exit early
    await agent.send_text("hello")
    assert len(send_fn.messages) == 0


@pytest.mark.asyncio
async def test_voice_agent_close_no_tasks():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    await agent.close()
    assert agent._closed is True


@pytest.mark.asyncio
async def test_voice_agent_touch_updates_activity():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    await asyncio.sleep(0.1)
    assert agent.idle_seconds >= 0.1
    agent.touch()
    assert agent.idle_seconds < 0.05


@pytest.mark.asyncio
async def test_voice_agent_screenshot_overwrites():
    from agents.voice_agent import VoiceAgent
    send_fn = FakeSendFn()
    agent = VoiceAgent(send_to_client=send_fn)
    agent.on_screenshot({"image": "first"})
    agent.on_screenshot({"image": "second"})
    assert agent._screenshot_data["image"] == "second"
    assert agent._screenshot_event.is_set()


@pytest.mark.asyncio
async def test_voice_agent_tool_labels_exist():
    from agents.voice_agent import _TOOL_LABELS
    assert "browse_web" in _TOOL_LABELS
    assert "read_page" in _TOOL_LABELS
