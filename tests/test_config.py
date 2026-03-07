"""Tests for backend configuration module."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_models_configured():
    from config import LIVE_API_MODEL, COMPUTER_USE_MODEL
    assert "gemini" in LIVE_API_MODEL
    assert "computer-use" in COMPUTER_USE_MODEL


def test_audio_settings():
    from config import INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE, AUDIO_CHANNELS
    assert INPUT_SAMPLE_RATE == 16000
    assert OUTPUT_SAMPLE_RATE == 24000
    assert AUDIO_CHANNELS == 1


def test_session_limits():
    from config import MAX_CONCURRENT_SESSIONS, SESSION_IDLE_TIMEOUT
    assert MAX_CONCURRENT_SESSIONS == 3
    assert SESSION_IDLE_TIMEOUT == 600


def test_browse_limits():
    from config import MAX_BROWSE_STEPS, SCREENSHOT_TIMEOUT, ACTION_TIMEOUT
    assert MAX_BROWSE_STEPS == 10
    assert SCREENSHOT_TIMEOUT == 15
    assert ACTION_TIMEOUT == 30


def test_system_prompt_exists():
    from config import SYSTEM_PROMPT
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0
    lower = SYSTEM_PROMPT.lower()
    assert "browse" in lower or "accessibility" in lower


def test_audio_format_is_pcm():
    from config import AUDIO_FORMAT
    assert "pcm" in AUDIO_FORMAT.lower()


def test_backend_port_is_int():
    from config import BACKEND_PORT
    assert isinstance(BACKEND_PORT, int)


def test_screenshot_quality_valid():
    from config import SCREENSHOT_QUALITY
    assert (isinstance(SCREENSHOT_QUALITY, int) and 0 <= SCREENSHOT_QUALITY <= 100) or \
           (isinstance(SCREENSHOT_QUALITY, float) and 0 <= SCREENSHOT_QUALITY <= 1)
