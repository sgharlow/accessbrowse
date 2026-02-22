"""AccessBrowse backend — FastAPI + WebSocket server for voice-driven web browsing."""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import BACKEND_PORT, MAX_CONCURRENT_SESSIONS
from services.session_manager import SessionManager
from agents.voice_agent import VoiceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("accessbrowse")

sessions = SessionManager(max_sessions=MAX_CONCURRENT_SESSIONS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    sessions.start_cleanup_loop()
    yield
    # Shutdown
    await sessions.cleanup_all()


app = FastAPI(title="AccessBrowse", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_sessions": sessions.active_count,
        "max_sessions": MAX_CONCURRENT_SESSIONS,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    sid = str(uuid.uuid4())
    logger.info(f"WebSocket connected: {sid}")

    async def send_to_client(msg: dict):
        try:
            await ws.send_json(msg)
        except Exception as e:
            logger.debug(f"Failed to send to client {sid}: {e}")

    try:
        async for raw in ws.iter_text():
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "start_session":
                if sessions.at_capacity:
                    await send_to_client({"type": "error", "message": "Server at capacity. Try again later."})
                    continue

                session_id = str(uuid.uuid4())
                logger.info(f"Starting session {session_id} for {sid}")

                try:
                    agent = VoiceAgent(send_to_client=send_to_client)
                    await agent.start()
                    sessions.add(sid, session_id, agent)
                    await send_to_client({"type": "session_started", "session_id": session_id})
                except Exception as e:
                    logger.error(f"Failed to start session: {e}")
                    await send_to_client({"type": "error", "message": "Failed to start session."})

            elif msg_type == "stop_session":
                await send_to_client({"type": "session_stopped"})
                asyncio.create_task(sessions.cleanup(sid))

            elif msg_type == "audio_chunk":
                session = sessions.get_by_sid(sid)
                if session:
                    audio_b64 = msg.get("data", "")
                    if audio_b64:
                        await session["agent"].send_audio(audio_b64)

            elif msg_type == "text_input":
                session = sessions.get_by_sid(sid)
                if session:
                    text = msg.get("text", "")
                    if text:
                        await session["agent"].send_text(text)

            elif msg_type == "page_screenshot":
                session = sessions.get_by_sid(sid)
                if session:
                    session["agent"].on_screenshot(msg)

            elif msg_type == "action_result":
                session = sessions.get_by_sid(sid)
                if session:
                    session["agent"].on_action_result(msg)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {sid}")
    except Exception as e:
        logger.error(f"WebSocket error for {sid}: {e}")
    finally:
        await sessions.cleanup(sid)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
