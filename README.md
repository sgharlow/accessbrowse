# AccessBrowse — Voice-Driven Web Browser for Accessibility

> Browse any website using voice commands. Built for visually impaired users
> with Gemini Live API (real-time voice) and Gemini Computer Use (visual browsing).

## What It Does

Over 2.2 billion people worldwide have some form of visual impairment, yet the web remains overwhelmingly visual. Screen readers help with text content, but they struggle with modern single-page applications, dynamic layouts, and interactive elements that rely on visual context. Users who are blind or have low vision face constant barriers when trying to search for apartments, shop for products, or simply read the news.

AccessBrowse eliminates these barriers by turning any website into a voice conversation. A user says "Find me apartments in Seattle under $1000 on Zillow," and AccessBrowse handles every step: navigating to the site, typing in search criteria, scrolling through results, and reading back the most relevant listings — all through natural, real-time voice interaction. There is no need to understand page structure, find specific buttons, or interpret visual layouts.

The key technical innovation is **coordinate-based browsing**. Instead of relying on CSS selectors or DOM queries (which break across websites and fail on dynamic content), AccessBrowse uses Gemini Computer Use to analyze page screenshots and return precise (x, y) coordinates on a normalized 1000x1000 grid. The content script then translates these coordinates to viewport pixels and executes the action via `document.elementFromPoint()`. This approach works on any website without site-specific configuration. Combined with Gemini Live API for bidirectional voice streaming at 24kHz output quality and a fully async Python backend, AccessBrowse delivers a seamless, conversational browsing experience with 13 distinct action types including click, type, scroll, hover, drag, and keyboard input.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  User's Chrome Browser                   │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Sidepanel   │  │  Service    │  │  Content Script  │  │
│  │  React + TS  │  │  Worker     │  │  Coordinate DOM  │  │
│  │  Transcript  │◄►│  WebSocket  │◄►│  Actions (13)    │  │
│  │  Controls    │  │  Client     │  │  elementFromPoint│  │
│  └─────────────┘  └──────┬──────┘  └─────────────────┘  │
│                          │                               │
│  ┌─────────────────────┐ │                               │
│  │  Offscreen Document │ │                               │
│  │  Mic 16kHz In       │◄┘                               │
│  │  Speaker 24kHz Out  │                                 │
│  └─────────────────────┘                                 │
└──────────────────────────┬───────────────────────────────┘
                           │ WebSocket (Audio + Text + Screenshots)
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  Google Cloud Run                        │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │  FastAPI          │  │  Voice Agent                 │  │
│  │  WebSocket Server │─►│  GenAI SDK Live API Client   │  │
│  │                   │  │  Tool Declarations           │  │
│  └──────────────────┘  └──────────┬───────────────────┘  │
│                                   │                      │
│  ┌──────────────┐  ┌──────────────┴───────────────────┐  │
│  │ Session Mgr  │  │  Tools                           │  │
│  │ Max 3 conc.  │  │  browse_web: multi-step loop     │  │
│  │ Idle cleanup │  │  read_page: a11y summaries       │  │
│  └──────────────┘  │  action_planner: coord planning  │  │
│                     └─────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │ Vertex AI API
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Google Cloud / Vertex AI                    │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Gemini Live API (gemini-2.5-flash-native-audio)  │   │
│  │  Bidirectional voice streaming + tool calling     │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Gemini Computer Use (gemini-2.5-computer-use)    │   │
│  │  Screenshot analysis → coordinate-based actions   │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

**Components:**
- **Chrome Extension (MV3):** Sidepanel UI, audio pipeline, screenshot capture, DOM actions
- **FastAPI Backend:** WebSocket server, Gemini Live API voice streaming, Computer Use vision
- **Google Cloud:** Cloud Run (hosting), Vertex AI (Gemini model access)

**Tech Stack:**
- Backend: Python 3.12, FastAPI, Google GenAI SDK, Vertex AI
- Extension: TypeScript, React 18, Vite, Web Audio API, Chrome MV3
- Deployment: Cloud Run, Docker

## Prerequisites

- Python 3.12+
- Node.js 20+
- Google Chrome (latest)
- Google Cloud account with billing enabled
- `gcloud` CLI installed ([install guide](https://cloud.google.com/sdk/docs/install))

## Quick Start (Local Development)

### 1. Clone and set up backend

```bash
git clone https://github.com/sgharlow/accessbrowse.git
cd accessbrowse

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Set up GCP authentication
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Copy environment config
cp .env.example .env
# Edit .env with your GCP project ID
```

### 2. Enable required GCP APIs

```bash
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  generativelanguage.googleapis.com
```

### 3. Start the backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

The server starts at `http://localhost:8080`. Verify with:

```bash
curl http://localhost:8080/health
# Expected: {"status":"ok","active_sessions":0,"max_sessions":3}
```

### 4. Build the Chrome extension

```bash
# Build the service worker
cd extension
npm install
npm run build

# Build the sidepanel
cd sidepanel
npm install
npm run build
cd ../..
```

### 5. Load the extension in Chrome

1. Open `chrome://extensions`
2. Enable **"Developer mode"** (toggle in top right)
3. Click **"Load unpacked"**
4. Select the `extension/` folder
5. The AccessBrowse icon appears in your toolbar

### 6. Use AccessBrowse

1. Click the AccessBrowse icon to open the sidepanel
2. Click **"Start Session"** to connect
3. Click **"Speak"** and say: *"Search for apartments in Seattle on Zillow"*
4. Watch AccessBrowse navigate, search, and read results back to you

## Cloud Run Deployment

```bash
# Deploy to Google Cloud Run
chmod +x backend/deploy.sh
./backend/deploy.sh
```

After deployment, update the extension to point to your production URL:

```bash
# The deploy script prints the Cloud Run URL
# Update via Chrome extension storage or background.js BACKEND_URL_KEY
```

See `backend/deploy.sh` for the full Infrastructure-as-Code deployment script.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Python unit tests (backend)
python -m pytest tests/ -v

# Content script tests
node tests/test_content_actions.js

# E2E tests (requires running backend)
cd tests/e2e && node test_session_lifecycle.js
```

## Project Structure

```
accessbrowse/
├── backend/
│   ├── main.py              # FastAPI WebSocket server
│   ├── config.py            # GCP model IDs, audio settings
│   ├── agents/
│   │   └── voice_agent.py   # Gemini Live API bidi-streaming
│   ├── services/
│   │   └── session_manager.py # Concurrency control, idle cleanup
│   ├── tools/
│   │   ├── action_planner.py # Computer Use → coordinates
│   │   ├── browse_web.py     # Multi-step browser automation
│   │   └── read_page.py      # Accessibility page summaries
│   ├── requirements.txt
│   ├── Dockerfile
│   └── deploy.sh            # Cloud Run IaC deployment
├── extension/
│   ├── manifest.json         # Chrome MV3 manifest
│   ├── background.js         # Service worker + WebSocket
│   ├── content.js            # Coordinate-based DOM actions
│   ├── offscreen.js          # 16kHz capture / 24kHz playback
│   └── sidepanel/            # React + TypeScript UI
│       └── src/
│           ├── App.tsx
│           └── components/
├── tests/
│   ├── test_*.py             # Python unit tests
│   ├── test_content_actions.js
│   └── e2e/                  # End-to-end integration tests
├── docs/
│   └── plans/
└── .env.example
```

## Hackathon

Built for the [Gemini Live Agent Challenge](https://googleliveagentchallenge.devpost.com/)

**Track:** UI Navigator | **Category:** Gemini Live API + Gemini Computer Use

**Key GCP Services Used:**
- Gemini Live API (`gemini-2.5-flash-native-audio`) — real-time bidirectional voice streaming with tool calling
- Gemini Computer Use (`gemini-2.5-computer-use`) — screenshot analysis returning coordinate-based actions
- Cloud Run — serverless container hosting for the FastAPI backend
- Vertex AI — model access and authentication
