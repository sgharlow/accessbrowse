# backend/tools/action_planner.py
"""Action Planner — uses Gemini Computer Use model to analyze screenshots
and return coordinate-based actions.

Key improvement over AccessVoice: returns (x,y) coordinates on a 1000x1000
normalized grid instead of CSS selectors. Eliminates the 20-30% selector
accuracy failure rate.
"""

import json
import base64
import logging

from config import PROJECT_ID, LOCATION, COMPUTER_USE_MODEL

logger = logging.getLogger("accessbrowse.tools.action_planner")

ACTION_PROMPT = """You are a web browsing agent helping a visually impaired user.

Goal: {goal}
Current URL: {url}

Analyze this screenshot and return the SINGLE next action to achieve the goal.

Return ONLY a JSON object with one of these formats:
{{"action": "click", "coordinate": [x, y]}}
{{"action": "type", "coordinate": [x, y], "text": "..."}}
{{"action": "scroll", "coordinate": [x, y], "direction": "down", "amount": 3}}
{{"action": "key", "key": "Escape"}}
{{"action": "hover", "coordinate": [x, y]}}
{{"action": "go_back"}}
{{"action": "wait", "duration": 2}}
{{"action": "done", "summary": "Natural language summary of what was found..."}}

Coordinates are on a 1000x1000 normalized grid where (0,0) is top-left and (1000,1000) is bottom-right.
When the goal is achieved or results are visible, return "done" with a clear, accessible summary.
If you need to type in a search box, first click on it, then type."""


def _parse_action_response(raw: str) -> dict:
    """Parse model response, handling markdown code blocks and invalid JSON."""
    text = raw.strip()

    # Strip markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        if inner.startswith("json"):
            inner = inner[4:]
        text = inner.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse action response: {text[:100]}")
        return {"action": "done", "summary": f"I had trouble analyzing the page. Raw response: {text[:200]}"}


async def plan_action(screenshot_b64: str, goal: str, url: str = "") -> dict:
    """Analyze screenshot with Gemini Computer Use and determine next action.

    Args:
        screenshot_b64: Base64-encoded JPEG screenshot
        goal: What the user wants to accomplish
        url: Current page URL

    Returns:
        dict with 'action' key and action-specific parameters
    """
    from google import genai

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    prompt = ACTION_PROMPT.format(goal=goal, url=url)

    try:
        response = await client.aio.models.generate_content(
            model=COMPUTER_USE_MODEL,
            contents=[{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": screenshot_b64}},
                    {"text": prompt},
                ],
            }],
            config={"temperature": 0.1, "max_output_tokens": 500},
        )

        result = _parse_action_response(response.text)
        logger.info(f"Action planned: {result.get('action')} for goal: {goal[:50]}")
        return result

    except Exception as e:
        logger.error(f"Action planning failed: {e}")
        return {"action": "done", "summary": f"I had trouble analyzing the page: {str(e)}"}
