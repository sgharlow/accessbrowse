# tests/test_action_planner.py
"""Tests for action planner — Gemini Computer Use integration."""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_action_prompt_has_required_actions():
    from tools.action_planner import ACTION_PROMPT
    for action in ["click", "type", "scroll", "key", "hover", "go_back", "wait", "done"]:
        assert action in ACTION_PROMPT, f"Missing action '{action}' in ACTION_PROMPT"


def test_action_prompt_has_coordinate_format():
    from tools.action_planner import ACTION_PROMPT
    assert "coordinate" in ACTION_PROMPT
    assert "1000" in ACTION_PROMPT  # Normalized grid reference


def test_parse_action_response_click():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "click", "coordinate": [450, 320]}'
    result = _parse_action_response(raw)
    assert result["action"] == "click"
    assert result["coordinate"] == [450, 320]


def test_parse_action_response_done():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "done", "summary": "Found 5 results"}'
    result = _parse_action_response(raw)
    assert result["action"] == "done"
    assert result["summary"] == "Found 5 results"


def test_parse_action_response_markdown_wrapped():
    from tools.action_planner import _parse_action_response
    raw = '```json\n{"action": "scroll", "coordinate": [500, 500], "direction": "down", "amount": 3}\n```'
    result = _parse_action_response(raw)
    assert result["action"] == "scroll"


def test_parse_action_response_invalid():
    from tools.action_planner import _parse_action_response
    raw = "I don't know what to do"
    result = _parse_action_response(raw)
    assert result["action"] == "done"
    assert "summary" in result


def test_parse_action_response_type_action():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "type", "coordinate": [300, 200], "text": "hello world"}'
    result = _parse_action_response(raw)
    assert result["action"] == "type"
    assert result["coordinate"] == [300, 200]
    assert result["text"] == "hello world"


def test_parse_action_response_scroll_with_amount():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "scroll", "coordinate": [500, 500], "direction": "up", "amount": 5}'
    result = _parse_action_response(raw)
    assert result["action"] == "scroll"
    assert result["direction"] == "up"
    assert result["amount"] == 5


def test_parse_action_response_key_action():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "key", "key": "Escape"}'
    result = _parse_action_response(raw)
    assert result["action"] == "key"
    assert result["key"] == "Escape"


def test_parse_action_response_hover():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "hover", "coordinate": [750, 250]}'
    result = _parse_action_response(raw)
    assert result["action"] == "hover"
    assert result["coordinate"] == [750, 250]


def test_parse_action_response_go_back():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "go_back"}'
    result = _parse_action_response(raw)
    assert result["action"] == "go_back"


def test_parse_action_response_wait():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "wait", "duration": 3}'
    result = _parse_action_response(raw)
    assert result["action"] == "wait"
    assert result["duration"] == 3


def test_parse_action_response_markdown_no_json_prefix():
    from tools.action_planner import _parse_action_response
    raw = '```\n{"action": "click", "coordinate": [100, 100]}\n```'
    result = _parse_action_response(raw)
    assert result["action"] == "click"
    assert result["coordinate"] == [100, 100]


def test_parse_action_response_whitespace_padded():
    from tools.action_planner import _parse_action_response
    raw = '  \n\n  {"action": "click", "coordinate": [200, 300]}  \n\n  '
    result = _parse_action_response(raw)
    assert result["action"] == "click"
    assert result["coordinate"] == [200, 300]


def test_action_prompt_template_substitution():
    from tools.action_planner import ACTION_PROMPT
    rendered = ACTION_PROMPT.format(goal="test goal", url="https://x.com")
    assert "test goal" in rendered
    assert "https://x.com" in rendered


def test_parse_nested_code_block():
    from tools.action_planner import _parse_action_response
    raw = '```json\n{"action": "done", "summary": "found ```code``` in page"}\n```'
    result = _parse_action_response(raw)
    assert result["action"] == "done"
    assert "```code```" in result["summary"]


def test_parse_empty_string():
    from tools.action_planner import _parse_action_response
    result = _parse_action_response("")
    assert result["action"] == "done"
    assert "trouble" in result["summary"].lower()


def test_parse_just_backticks():
    from tools.action_planner import _parse_action_response
    result = _parse_action_response("```\n```")
    assert result["action"] == "done"


def test_action_prompt_format_substitution():
    from tools.action_planner import ACTION_PROMPT
    rendered = ACTION_PROMPT.format(goal="test goal", url="http://example.com")
    assert "test goal" in rendered
    assert "http://example.com" in rendered


def test_parse_valid_json_with_extra_fields():
    from tools.action_planner import _parse_action_response
    raw = '{"action": "click", "coordinate": [100, 200], "extra_field": "extra_value", "debug": true}'
    result = _parse_action_response(raw)
    assert result["action"] == "click"
    assert result["coordinate"] == [100, 200]
    assert result["extra_field"] == "extra_value"
    assert result["debug"] is True
