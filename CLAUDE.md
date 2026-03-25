# CLAUDE.md
This file provides guidance to Claude Code when working with this repository.

## Project Overview
AccessBrowse is a voice-driven web browser for accessibility that lets visually impaired users browse any website using voice commands. It uses Gemini Live API for real-time bidirectional voice and Gemini Computer Use for coordinate-based visual browsing, implemented as a Chrome Extension with a Python backend.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Google GenAI SDK, Vertex AI
- **Extension**: TypeScript, React 18, Vite, Web Audio API, Chrome Manifest V3
- **AI Models**: Gemini Live API (gemini-2.5-flash-native-audio), Gemini Computer Use (gemini-2.5-computer-use)
- **Deployment**: Google Cloud Run, Docker
- **Testing**: pytest, pytest-asyncio, custom E2E suite

## Project Structure
```
accessbrowse/
├── backend/
│   ├── main.py              # FastAPI WebSocket server
│   ├── config.py            # GCP model IDs, audio settings
│   ├── agents/voice_agent.py # Gemini Live API bidi-streaming
│   ├── services/session_manager.py # Concurrency control
│   ├── tools/               # action_planner, browse_web, read_page
│   ├── requirements.txt
│   ├── Dockerfile
│   └── deploy.sh            # Cloud Run IaC deployment
├── extension/
│   ├── manifest.json         # Chrome MV3 manifest
│   ├── background.js         # Service worker + WebSocket
│   ├── content.js            # Coordinate-based DOM actions
│   ├── offscreen.js          # 16kHz capture / 24kHz playback
│   └── sidepanel/            # React + TypeScript UI
├── tests/                    # Python unit tests + E2E tests
├── docs/plans/
└── .env.example
```

## Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Extension build
cd extension && npm install && npm run build
cd sidepanel && npm install && npm run build

# Run tests (107 tests across 7 suites)
python -m pytest tests/ -v

# Content script tests
node tests/test_content_actions.js
```

## Key Information
- Requires GCP authentication: `gcloud auth application-default login`
- Production URL: `https://accessbrowse-n6oitfxdra-uc.a.run.app`
- The key innovation is coordinate-based browsing using a normalized 1000x1000 grid
- 13 distinct action types: click, type, scroll, hover, drag, keyboard input, etc.
- Built for the Gemini Live Agent Challenge hackathon (submitted)
- Load extension via `chrome://extensions` > Developer mode > Load unpacked > `extension/`
