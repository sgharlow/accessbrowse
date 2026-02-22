# Building AccessBrowse: Voice-Driven Web Browsing with Gemini AI

*This blog post was created for the Gemini Live Agent Challenge hackathon.*

**#GeminiLiveAgentChallenge**

---

## The Problem: The Web Is Built for Eyes

Over 2.2 billion people worldwide live with visual impairment. Despite decades of work on web accessibility standards, the practical reality for many users who are blind or have low vision is an internet full of barriers. Screen readers do their best, but they hit walls with modern web applications: dynamic JavaScript layouts, single-page apps that never reload, interactive elements that only make visual sense, and websites that neglect ARIA attributes entirely.

The fundamental issue is that most assistive tools try to understand the web through its source code — parsing the DOM, following ARIA roles, reading element text. This works for well-structured, semantic HTML. It fails on the messy, JavaScript-heavy reality of the modern web.

We wanted to try a different approach: what if we looked at websites the same way a sighted person does — visually — and combined that with natural voice conversation?

## The Approach: Coordinate-Based Browsing

The core insight behind AccessBrowse is simple: instead of parsing the DOM, take a screenshot and ask an AI model what it sees. This is exactly what Gemini Computer Use is designed for.

Here is the action loop at the heart of AccessBrowse:

1. The user speaks a request ("Find me apartments in Seattle under $1000 on Zillow")
2. Gemini Live API receives the voice input and decides to call the `browse_web` tool
3. The backend requests a screenshot from the Chrome extension
4. The screenshot is sent to Gemini Computer Use (`gemini-2.5-computer-use`)
5. The model analyzes the visual content and returns the next action with precise coordinates
6. The content script translates coordinates to viewport pixels and executes the action
7. Steps 3-6 repeat until the task is complete

The coordinates come back on a **normalized 1000x1000 grid** — (0, 0) is the top-left corner, (1000, 1000) is the bottom-right. This abstraction is powerful because it works regardless of the actual viewport size. Whether the browser window is 1280 pixels wide or 1920 pixels wide, coordinate (500, 300) always refers to the same relative position on the page.

On the extension side, translating these coordinates to actual DOM interactions is straightforward:

```javascript
const x = (coordinate[0] / 1000) * window.innerWidth;
const y = (coordinate[1] / 1000) * window.innerHeight;
const element = document.elementFromPoint(x, y);
element.click();
```

This `document.elementFromPoint()` approach eliminates the fragility of CSS selector matching. The model does not need to guess at class names or XPath expressions. It looks at the page, identifies the button or form field visually, and returns where to click. In practice, this works on sites ranging from Zillow's complex map-and-list layout to Amazon's product grid to CNN's news feed.

## The Voice Pipeline: Gemini Live API

AccessBrowse uses Gemini Live API (`gemini-2.5-flash-native-audio`) for real-time bidirectional voice streaming. The connection is established using the Google GenAI SDK:

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

config = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
    system_instruction=types.Content(parts=[types.Part(text=SYSTEM_PROMPT)]),
    tools=[tool_obj],
)

session = client.aio.live.connect(model=LIVE_API_MODEL, config=config)
live = await session.__aenter__()
```

The session is a full bidi-stream: audio frames flow in (16kHz PCM from the microphone), and audio responses flow out (24kHz PCM from Gemini). The 24kHz output was a deliberate choice — for a product where the user experience is entirely audio-driven, voice quality matters enormously. The difference between 16kHz and 24kHz is clearly audible in consonant clarity and natural intonation.

### Tool Calling Within Live Sessions

One of the most interesting engineering challenges was tool calling within the streaming session. When Gemini decides the user wants to browse a website, it emits a `tool_call` in the response stream. The backend must:

1. Receive the tool call (with function name and arguments)
2. Execute the tool (which may involve 10+ steps of screenshot-analyze-act)
3. Return the tool result as a `LiveClientToolResponse`
4. Resume processing the audio stream as Gemini speaks the result

This happens within a single async event loop. The `browse_web` tool execution can take 30+ seconds (multiple screenshots, model calls, and DOM actions), and during this time the Live API connection must stay alive. We solve this with a keepalive task that sends 100ms of silence at 200ms intervals:

```python
async def _audio_keepalive(self):
    while True:
        await asyncio.sleep(0.2)
        if self._live:
            await self._live.send(
                input=types.LiveClientRealtimeInput(
                    media_chunks=[types.Blob(
                        data=silence_bytes,
                        mime_type="audio/pcm;rate=16000",
                    )]
                )
            )
```

## The Audio Pipeline: Web Audio API in a Chrome Extension

Chrome MV3 extensions have a constraint that made the audio pipeline interesting: service workers cannot access the DOM, which means no `AudioContext` or `getUserMedia()` in the service worker. The solution is an **offscreen document** — a hidden page created by the extension specifically for audio processing.

The offscreen document handles both microphone capture and audio playback:

- **Capture:** `getUserMedia()` with 16kHz sample rate, mono, echo cancellation enabled. Audio frames are captured via a `ScriptProcessorNode`, converted from Float32 to Int16 PCM, base64-encoded, and sent to the service worker via `chrome.runtime.sendMessage()`.
- **Playback:** Incoming 24kHz PCM audio from Gemini is decoded from base64, converted to Float32, loaded into an `AudioBuffer` at 24000Hz sample rate, and played through a queued source node system for smooth sequential playback.

The key detail is the **sample rate asymmetry**: input is 16kHz (what Gemini Live API expects for speech input) while output is 24kHz (what Gemini outputs for higher quality). The offscreen document uses two separate `AudioContext` instances at different sample rates to handle this cleanly.

## Deployment: Cloud Run

The FastAPI backend is deployed to Google Cloud Run using a single deploy script (`deploy.sh`):

```bash
gcloud run deploy accessbrowse \
    --source ./backend \
    --project $PROJECT_ID \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300
```

Cloud Run is well-suited for this workload because the backend is stateful (WebSocket sessions) but not long-lived — sessions typically last 5-10 minutes. The 300-second timeout accommodates long browsing sessions, and 1Gi of memory is sufficient for the async Python server handling up to 3 concurrent sessions.

## What We Learned

**Vision-based interaction is more robust than DOM parsing.** Gemini Computer Use consistently identifies form fields, buttons, and links from screenshots — even on pages with complex layouts, overlapping elements, or minimal semantic markup. The coordinate-based approach eliminates an entire category of bugs related to CSS selector matching.

**The GenAI SDK makes Live API integration clean, but tool calling documentation is sparse.** The `client.aio.live.connect()` context manager pattern is elegant, and the `types.FunctionDeclaration` system for registering tools is straightforward. However, the documentation around executing tool calls within a live bidi-streaming session was minimal at the time of development, so we relied heavily on experimentation.

**Audio quality is a feature, not a nice-to-have.** For users who rely on voice as their primary interface, the difference between 16kHz and 24kHz output is immediately noticeable. Investing in the higher sample rate was one of the best decisions we made.

## Try It Yourself

AccessBrowse is open source: [github.com/sgharlow/accessbrowse](https://github.com/sgharlow/accessbrowse)

The README includes step-by-step setup instructions. You need a Google Cloud account with Vertex AI enabled, Python 3.12+, Node.js 20+, and Google Chrome.

---

*Built with Google Gemini Live API, Gemini Computer Use, Cloud Run, and Vertex AI for the [Gemini Live Agent Challenge](https://googleliveagentchallenge.devpost.com/).*

**#GeminiLiveAgentChallenge**
