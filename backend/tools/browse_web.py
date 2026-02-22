# backend/tools/browse_web.py
"""Browse tool — multi-step browser automation via Chrome extension.

Orchestrates: request screenshot -> plan action (Computer Use) -> execute action -> repeat.

Key difference from AccessVoice: uses asyncio.Event (not threading.Event) and
coordinate-based actions (not CSS selectors).
"""

import asyncio
import logging

from config import MAX_BROWSE_STEPS, SCREENSHOT_TIMEOUT, ACTION_TIMEOUT
from tools import action_planner

logger = logging.getLogger("accessbrowse.tools.browse_web")

# Settle delays (seconds) — allow page to render after navigation/action
_NAVIGATE_SETTLE = 3
_ACTION_SETTLE = 2


async def browse_web(
    url: str,
    task: str,
    send_to_client,
    screenshot_event: asyncio.Event,
    screenshot_data_ref,
    action_event: asyncio.Event,
    action_data_ref,
) -> str:
    """Navigate to a website and perform a task using the user's browser.

    Args:
        url: The website URL to navigate to
        task: What to do on the website
        send_to_client: async callable to send WebSocket messages
        screenshot_event: asyncio.Event set when screenshot arrives
        screenshot_data_ref: object with _screenshot_data dict attribute
        action_event: asyncio.Event set when action result arrives
        action_data_ref: object with _action_data dict attribute

    Returns:
        A summary of what was found or accomplished
    """
    await send_to_client({"type": "status", "message": f"Navigating to {url}..."})

    # Step 0: Navigate
    action_event.clear()
    await send_to_client({"type": "execute_action", "action": "navigate", "url": url})
    try:
        await asyncio.wait_for(action_event.wait(), timeout=ACTION_TIMEOUT)
    except asyncio.TimeoutError:
        pass  # Navigation may not always send action_result
    await asyncio.sleep(_NAVIGATE_SETTLE)  # Wait for page to settle

    # Steps 1-N: Screenshot -> analyze -> act -> repeat
    for step in range(MAX_BROWSE_STEPS):
        await send_to_client({"type": "status", "message": f"Step {step + 1}: analyzing page..."})

        # 1. Request screenshot
        screenshot_event.clear()
        await send_to_client({"type": "request_screenshot"})
        try:
            await asyncio.wait_for(screenshot_event.wait(), timeout=SCREENSHOT_TIMEOUT)
        except asyncio.TimeoutError:
            return "Failed to capture screenshot. Is the extension active?"

        screenshot = screenshot_data_ref._screenshot_data
        if not screenshot.get("image"):
            return "Failed to capture screenshot from browser."

        # 2. Ask Computer Use model for next action
        await send_to_client({"type": "status", "message": f"Step {step + 1}: deciding next action..."})

        action = await action_planner.plan_action(
            screenshot_b64=screenshot["image"],
            goal=task,
            url=screenshot.get("url", url),
        )

        logger.info(f"Step {step + 1}: {action}")

        # 3. Check if done
        if action.get("action") == "done":
            return action.get("summary", "Task completed.")

        # 4. Execute action
        await send_to_client({"type": "status", "message": f"Step {step + 1}: {_describe_action(action)}"})
        action_event.clear()
        await send_to_client({"type": "execute_action", **action})
        try:
            await asyncio.wait_for(action_event.wait(), timeout=ACTION_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Action timed out: {action.get('action')}")

        # 5. Brief pause for page to update
        await asyncio.sleep(_ACTION_SETTLE)

    return "Reached maximum steps. Here's what I found so far based on the page."


def _describe_action(action: dict) -> str:
    """Human-readable description of an action for status updates."""
    a = action.get("action", "")
    if a == "click":
        return f"clicking at ({action.get('coordinate', [0,0])})"
    if a == "type":
        return f"typing '{action.get('text', '')[:30]}'"
    if a == "scroll":
        return f"scrolling {action.get('direction', 'down')}"
    if a == "hover":
        return "hovering"
    if a == "key":
        return f"pressing {action.get('key', '')}"
    if a == "go_back":
        return "going back"
    if a == "wait":
        return "waiting for page"
    return a
