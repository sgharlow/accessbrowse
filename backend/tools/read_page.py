# backend/tools/read_page.py
"""read_page tool — accessibility-focused page summaries using Gemini vision."""

import asyncio
import logging

from config import PROJECT_ID, LOCATION, COMPUTER_USE_MODEL

logger = logging.getLogger("accessbrowse.tools.read_page")

READ_PROMPT = """Analyze this screenshot and provide an accessibility-friendly summary.

1. **Page Identity**: What website and page is this?
2. **Key Content**: Summarize the main content in natural, speech-friendly language.
   - Use spatial descriptions ("At the top...", "The main area shows...")
   - Describe quantities ("5 search results", "3 navigation links")
   - Never reference raw HTML, CSS, or technical markup
3. **Available Actions**: What can the user do next on this page?

Keep it concise but complete. This will be read aloud to a visually impaired user.
Focus on: {focus}"""


async def read_page(
    focus: str = "main content",
    send_to_client=None,
    screenshot_event=None,
    screenshot_data_ref=None,
    timeout: float = 15.0,
) -> str:
    """Get an accessibility-focused summary of the current page.

    Args:
        focus: What to focus on ('main content', 'search results', etc.)
        send_to_client: async callable to send WebSocket messages
        screenshot_event: asyncio.Event set when screenshot arrives
        screenshot_data_ref: object with _screenshot_data attribute
        timeout: seconds to wait for screenshot

    Returns:
        Accessibility-focused page description
    """
    if not send_to_client or not screenshot_event or not screenshot_data_ref:
        return "No connection to browser extension. Make sure the extension is installed and connected."

    await send_to_client({"type": "status", "message": "Reading page content..."})

    try:
        # Request screenshot
        screenshot_event.clear()
        await send_to_client({"type": "request_screenshot"})

        try:
            await asyncio.wait_for(screenshot_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return "I couldn't capture the current page. Please try again."

        screenshot = screenshot_data_ref._screenshot_data
        img_b64 = screenshot.get("image")
        if not img_b64:
            return "I couldn't capture the current page. Please try again."

        await send_to_client({"type": "status", "message": "Analyzing page content..."})

        # Send to Gemini for vision analysis
        from google import genai

        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

        response = await client.aio.models.generate_content(
            model=COMPUTER_USE_MODEL,
            contents=[{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                    {"text": READ_PROMPT.format(focus=focus)},
                ],
            }],
            config={"temperature": 0.3, "max_output_tokens": 1024},
        )

        summary = response.text
        await send_to_client({"type": "status", "message": "Responding..."})
        return summary or "I couldn't read the page content. Let me try again."

    except Exception as e:
        logger.error(f"Read page failed: {e}")
        err_msg = str(e).lower()
        if "timeout" in err_msg:
            return "The page analysis took too long. Would you like me to try a specific section?"
        return "I had trouble reading the page. Would you like me to try again?"
