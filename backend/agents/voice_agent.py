"""Voice agent — uses Google GenAI SDK for bidi-streaming voice with Gemini Live API.

Design decisions:
- asyncio.Event for cross-component sync (fully async, no threading)
- GenAI SDK client.aio.live.connect() for Live API session
- Tool declarations via types.FunctionDeclaration
- 24kHz output audio for higher quality voice
"""

import asyncio
import base64
import logging
import time
from typing import Callable, Optional

from config import (
    PROJECT_ID,
    LOCATION,
    LIVE_API_MODEL,
    INPUT_SAMPLE_RATE,
    AUDIO_FORMAT,
    SYSTEM_PROMPT,
)

logger = logging.getLogger("accessbrowse.voice")

# Friendly tool names for status updates
_TOOL_LABELS = {
    "browse_web": "Browsing the web",
    "read_page": "Reading the page",
}


class VoiceAgent:
    """Manages a Gemini Live API bidirectional voice session with tool calling."""

    def __init__(self, send_to_client: Callable):
        self._send = send_to_client  # async fn to send WebSocket JSON message
        self._screenshot_event = asyncio.Event()
        self._screenshot_data: dict = {}
        self._action_event = asyncio.Event()
        self._action_data: dict = {}
        self._session = None          # Gemini Live API session
        self._live = None             # Live API context
        self._receive_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._closed = False
        self._last_activity = time.monotonic()

        # 100ms of silence at 16kHz, 16-bit mono = 3200 bytes
        self._silence_b64 = base64.b64encode(b"\x00" * 3200).decode("utf-8")

    @property
    def idle_seconds(self) -> float:
        return time.monotonic() - self._last_activity

    def touch(self):
        self._last_activity = time.monotonic()

    async def start(self) -> None:
        """Start the Gemini Live API bidi-streaming session."""
        await self._send({"type": "status", "message": "Connecting to Gemini..."})

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

            # Import tools
            from tools.browse_web import browse_web
            from tools.read_page import read_page

            # Define tool declarations for Live API
            browse_web_decl = types.FunctionDeclaration(
                name="browse_web",
                description="Navigate to a website and perform a task using the user's browser. Use this when the user asks to search, shop, read news, or interact with any website.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "url": types.Schema(type="STRING", description="The website URL to navigate to"),
                        "task": types.Schema(type="STRING", description="What to do on the website"),
                    },
                    required=["url", "task"],
                ),
            )

            read_page_decl = types.FunctionDeclaration(
                name="read_page",
                description="Get an accessibility-focused summary of the current page. Use this when the user asks what's on screen or wants content read aloud.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "focus": types.Schema(
                            type="STRING",
                            description="What to focus on: 'main content', 'search results', 'navigation', etc.",
                        ),
                    },
                ),
            )

            tool_obj = types.Tool(function_declarations=[browse_web_decl, read_page_decl])

            config = types.LiveConnectConfig(
                response_modalities=["AUDIO", "TEXT"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                    )
                ),
                system_instruction=types.Content(
                    parts=[types.Part(text=SYSTEM_PROMPT)]
                ),
                tools=[tool_obj],
            )

            self._session = client.aio.live.connect(
                model=LIVE_API_MODEL,
                config=config,
            )

            # Enter the async context manager
            self._live = await self._session.__aenter__()

            # Spawn event loop and keepalive
            self._receive_task = asyncio.create_task(self._event_loop())
            self._keepalive_task = asyncio.create_task(self._audio_keepalive())

            await self._send({"type": "status", "message": "Connected — listening..."})
            logger.info("Gemini Live session started")

        except Exception as e:
            logger.error(f"Failed to start Gemini Live session: {e}")
            await self._send({"type": "status", "message": "Connection failed. Please try again."})
            raise

    async def _event_loop(self) -> None:
        """Process streaming responses from Gemini Live API."""
        try:
            while not self._closed and self._live:
                turn = self._live.receive()
                async for response in turn:
                    # Handle server content (audio + text)
                    if response.server_content:
                        sc = response.server_content
                        if sc.model_turn:
                            for part in sc.model_turn.parts:
                                if part.inline_data:
                                    # Audio chunk — forward to client
                                    audio_b64 = base64.b64encode(part.inline_data.data).decode()
                                    await self._send({"type": "audio", "data": audio_b64})
                                if part.text:
                                    # Transcript text
                                    await self._send({
                                        "type": "transcript",
                                        "role": "assistant",
                                        "text": part.text,
                                        "final": True,
                                    })
                        if sc.turn_complete:
                            await self._send({"type": "status", "message": "Listening..."})

                    # Handle tool calls
                    if response.tool_call:
                        await self._handle_tool_call(response.tool_call)

                    # Handle setup complete
                    if response.setup_complete:
                        logger.info("Gemini Live setup complete")

        except asyncio.CancelledError:
            logger.info("Event loop cancelled")
        except Exception as e:
            logger.error(f"Event loop error: {e}")
            if not self._closed:
                await self._send({"type": "status", "message": "Connection lost. Please restart."})

    async def _handle_tool_call(self, tool_call) -> None:
        """Execute tool calls from the Live API and send results back."""
        from google.genai import types
        from tools.browse_web import browse_web
        from tools.read_page import read_page

        results = []
        for fc in tool_call.function_calls:
            tool_name = fc.name
            args = dict(fc.args) if fc.args else {}
            label = _TOOL_LABELS.get(tool_name, tool_name)
            await self._send({"type": "status", "message": f"{label}..."})

            try:
                if tool_name == "browse_web":
                    result_text = await browse_web(
                        url=args.get("url", ""),
                        task=args.get("task", ""),
                        send_to_client=self._send,
                        screenshot_event=self._screenshot_event,
                        screenshot_data_ref=self,
                        action_event=self._action_event,
                        action_data_ref=self,
                    )
                elif tool_name == "read_page":
                    result_text = await read_page(
                        focus=args.get("focus", "main content"),
                        send_to_client=self._send,
                        screenshot_event=self._screenshot_event,
                        screenshot_data_ref=self,
                    )
                else:
                    result_text = f"Unknown tool: {tool_name}"
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                result_text = f"Tool failed: {str(e)}"

            results.append(types.FunctionResponse(
                name=tool_name,
                response={"result": result_text},
            ))

        # Send tool results back to Live API
        if self._closed or not self._live:
            return
        await self._live.send(
            input=types.LiveClientToolResponse(function_responses=results)
        )
        await self._send({"type": "status", "message": "Preparing response..."})

    async def _audio_keepalive(self) -> None:
        """Send silent audio frames to keep the Gemini Live connection alive."""
        try:
            from google.genai import types
            while True:
                await asyncio.sleep(0.2)
                if self._live:
                    await self._live.send(
                        input=types.LiveClientRealtimeInput(
                            media_chunks=[types.Blob(
                                data=base64.b64decode(self._silence_b64),
                                mime_type="audio/pcm;rate=16000",
                            )]
                        )
                    )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Keepalive stopped: {e}")

    async def send_audio(self, audio_b64: str) -> None:
        """Forward base64 PCM audio from client mic to Gemini Live API."""
        if self._closed or not self._live:
            return
        self._last_activity = time.monotonic()
        try:
            from google.genai import types
            audio_bytes = base64.b64decode(audio_b64)
            await self._live.send(
                input=types.LiveClientRealtimeInput(
                    media_chunks=[types.Blob(
                        data=audio_bytes,
                        mime_type="audio/pcm;rate=16000",
                    )]
                )
            )
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    async def send_text(self, text: str) -> None:
        """Forward text input to Gemini Live API."""
        if self._closed or not self._live:
            return
        self._last_activity = time.monotonic()
        try:
            from google.genai import types
            await self._live.send(
                input=types.LiveClientContent(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=text)],
                    )],
                    turn_complete=True,
                )
            )
        except Exception as e:
            logger.error(f"Error sending text: {e}")

    def on_screenshot(self, data: dict) -> None:
        """Handle screenshot response from extension."""
        self._screenshot_data = data
        self._screenshot_event.set()

    def on_action_result(self, data: dict) -> None:
        """Handle action result from extension content script."""
        self._action_data = data
        self._action_event.set()

    async def close(self) -> None:
        """Clean up the voice session."""
        self._closed = True
        for task in (self._keepalive_task, self._receive_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        if self._live:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing Live session: {e}")
        logger.info("Voice agent closed")
