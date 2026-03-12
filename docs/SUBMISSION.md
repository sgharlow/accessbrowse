# AccessBrowse — Devpost Submission

**Demo Video:** https://youtu.be/1BBzOFUTdKw
**Blog Post:** https://dev.to/steve_harlow_0dbc0e910b6d/building-accessbrowse-voice-driven-web-browsing-with-gemini-ai-5cj4
**IaC Deployment:** https://github.com/sgharlow/accessbrowse/blob/main/backend/deploy.sh
**GDG Profile:** https://gdg.community.dev/u/mcm396/#/about

## Inspiration

Over 2.2 billion people worldwide live with some form of visual impairment, according to the World Health Organization. Despite decades of progress in assistive technology, the modern web remains fundamentally visual. Single-page applications, dynamic JavaScript-driven layouts, and interactive elements that depend on visual context create constant barriers for users who are blind or have low vision. Traditional screen readers parse the DOM and read elements sequentially, but they struggle with complex layouts, overlapping content, and sites that rely on ARIA attributes that many developers never implement correctly.

We asked ourselves: what if a visually impaired user could simply *talk* to their browser the way they talk to a friend? "Find me apartments in Seattle under $1000 on Zillow." "Show me noise-canceling headphones on Amazon." "Read me today's top headlines." No need to navigate tab stops, learn keyboard shortcuts, or understand page structure. Just a conversation. Informed by prior accessibility research and a deep commitment to inclusive design, we set out to build a system that makes any website accessible through voice alone.

## What It Does

AccessBrowse is a voice-driven web browser built as a Chrome extension that fuses two Gemini modalities — real-time voice conversation and visual page understanding — into a single seamless experience. Users speak naturally, and AccessBrowse handles every step of web interaction: navigating to sites, clicking buttons, typing in search boxes, scrolling through results, and reading content back aloud. It works on any website without any site-specific configuration or special markup.

The multimodal UX is the core innovation: the user speaks (voice input via Gemini Live API), Gemini understands intent and manages the conversation (language understanding), Gemini Computer Use analyzes what's on screen (visual understanding), and the system speaks results back at 24kHz (voice output). These four modalities work together in a continuous loop — the user never leaves the voice conversation to interact with any website.

For example, a user says "Search for apartments in Seattle under $1000 on Zillow." AccessBrowse navigates to zillow.com, locates the search field by analyzing a screenshot, types the query using coordinate-based DOM interaction, applies filters, scrolls through results, and reads back the most relevant listings with prices, locations, and descriptions — all through natural voice conversation with real-time audio streaming. The sidepanel shows a live transcript and status updates so sighted users or observers can follow along.

## How We Built It

The system has two main components: a Python FastAPI backend deployed on Google Cloud Run, and a Chrome MV3 extension with four cooperating modules (service worker, content script, offscreen audio document, and React sidepanel).

The voice pipeline uses the **Gemini Live API** (`gemini-2.5-flash-native-audio`) via the Google GenAI SDK's `client.aio.live.connect()` for bidirectional audio streaming. Microphone audio is captured at 16kHz in the offscreen document, streamed over a WebSocket to the backend, and fed into the Live API session. Gemini's voice responses come back at 24kHz for higher-quality audio output and are played through the offscreen document's Web Audio API pipeline with a queued buffer system for smooth playback.

When Gemini determines the user wants to interact with a website, it calls one of two registered tools: `browse_web` or `read_page`. The `browse_web` tool runs a multi-step action loop: (1) request a screenshot from the Chrome extension via `chrome.tabs.captureVisibleTab`, (2) send the screenshot to **Gemini Computer Use** (`gemini-2.5-computer-use`) which analyzes the visual content and returns the next action as coordinates on a normalized 1000x1000 grid, (3) translate those coordinates to viewport pixels using `document.elementFromPoint()` in the content script, (4) execute the action, and (5) repeat until the task is complete or the maximum step count is reached. The `read_page` tool uses the same screenshot-to-vision pipeline but asks Gemini to generate an accessibility-focused summary of the page content.

The entire backend is fully async using Python asyncio, with `asyncio.Event` objects for cross-component synchronization. The session manager enforces a maximum of 3 concurrent sessions with idle timeout cleanup.

## Challenges We Ran Into

**Gemini Live API session management** was the biggest engineering challenge. The bidi-streaming connection requires careful lifecycle management — we needed keepalive audio frames (100ms of silence at 16kHz every 200ms) to prevent the connection from timing out, proper cleanup on disconnect, and graceful handling of mid-conversation tool calls. Getting the tool call flow right within the streaming context (receive tool call, pause audio, execute browse steps, return tool result, resume audio) required significant iteration.

**Coordinate accuracy** was another major challenge. Gemini Computer Use returns coordinates on a normalized grid, but the accuracy depends on screenshot quality, page zoom level, and the visual density of the page. We tuned the JPEG compression quality to 60% to balance file size against coordinate precision, and found that the 1000x1000 normalized grid with `document.elementFromPoint()` translation is remarkably robust across different viewport sizes and device pixel ratios.

**Audio latency** required careful optimization. The Web Audio API's `ScriptProcessorNode` introduces buffer latency, and the WebSocket round-trip adds network latency. We minimized perceived latency by having Gemini speak brief filler phrases ("Let me look that up...") before executing tool calls, so the user always hears immediate feedback.

## Accomplishments That We're Proud Of

We are most proud of the **coordinate-based action system** that works on any website without site-specific configuration. By using Gemini Computer Use for visual analysis instead of DOM parsing or CSS selectors, AccessBrowse avoids the 20-30% failure rate that selector-based approaches suffer on modern dynamic websites. The system supports **13 distinct action types**: click, type, scroll, hover, key press, drag, select, go back, go forward, navigate, wait, read page, and done.

The **fully async architecture** is another accomplishment. Every component — from the audio pipeline to the WebSocket server to the Gemini API calls to the screenshot relay — runs on async event loops with no blocking operations. This lets a single Cloud Run instance handle **3 concurrent voice browsing sessions** simultaneously with idle timeout cleanup.

The **engineering rigor**: 107 Python unit tests across 7 suites, 38 content script tests covering all 9 action types, end-to-end integration tests, GitHub Actions CI pipeline, Infrastructure-as-Code deployment via `deploy.sh`, and a fully containerized backend. The codebase is production-grade, not a hackathon prototype.

The **24kHz audio output** quality is noticeably better than the 16kHz baseline. For a product where the user experience is entirely audio-driven, voice quality matters enormously. We chose the Aoede voice for its clarity and natural cadence, and the 24kHz sample rate delivers noticeably clearer consonants and more natural intonation.

## What We Learned

Building with the **Gemini Computer Use coordinate system** taught us that vision-based interaction is surprisingly reliable. The model consistently identifies form fields, buttons, links, and interactive elements from screenshots alone. The key insight is that the normalized 1000x1000 grid abstracts away viewport size entirely — the same coordinate response works whether the browser is 1280px or 1920px wide.

We learned that **Gemini Live API tool calling** within a bidi-streaming session requires a specific flow: the model emits a `tool_call` response, you must execute the tool and return a `LiveClientToolResponse`, and then the model continues generating. Getting this right within an async event loop that is simultaneously handling audio input and output was the core engineering challenge. The GenAI SDK's `client.aio.live.connect()` context manager pattern is clean, but the documentation around tool calling within live sessions was sparse, so we relied heavily on experimentation.

We also learned practical lessons about **Chrome MV3 constraints**: service workers have no DOM access (requiring an offscreen document for audio), `chrome.tabs.captureVisibleTab` requires the `activeTab` permission and the tab must be visible, and message passing between extension components is strictly JSON-serializable (so base64 encoding is the practical choice for audio and image data).

## Try It Yourself

1. Clone the repo: `git clone https://github.com/sgharlow/accessbrowse.git`
2. Load the `extension/` folder in Chrome (`chrome://extensions` → Developer mode → Load unpacked)
3. Navigate to any website (Amazon, Zillow, CNN, Wikipedia — anything works)
4. Click the AccessBrowse icon → sidepanel opens → click **"Start Session"**
5. Click the mic button and say: *"Find me noise-canceling headphones on Amazon"*
6. Watch the page navigate autonomously — clicks, types, scrolls — then hear Gemini speak the results back at 24kHz

The backend is live on Google Cloud Run at `accessbrowse-n6oitfxdra-uc.a.run.app`. No configuration needed — the extension connects to production automatically.

**Verify backend health:** `curl https://accessbrowse-n6oitfxdra-uc.a.run.app/health`

## What's Next

**Multi-tab browsing** is the most requested feature — allowing AccessBrowse to open comparison tabs (e.g., two apartment listings side by side) and switch between them via voice commands.

**User preference memory** would let the system remember that a user prefers apartments with a dishwasher or always wants search results sorted by price. This could use Gemini's context window to maintain a running preference model.

**Chrome Web Store publication** is the natural distribution path. We plan to polish the extension UI, add an onboarding tutorial, and submit to the Chrome Web Store so anyone can install AccessBrowse with one click.

**Expanded action vocabulary** with form auto-fill, file upload support, and multi-select dropdowns would make AccessBrowse handle even more complex web workflows like filling out job applications or submitting government forms.
