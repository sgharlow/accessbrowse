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
