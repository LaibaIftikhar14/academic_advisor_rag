# backend/main.py
# ─────────────────────────────────────────────
# FastAPI Application — Assignment 4 Final Version
#
# Endpoints:
#   WS   /ws/chat              — text chat
#   WS   /ws/voice             — voice pipeline
#   GET  /health               — system status
#   POST /voice/transcribe     — ASR only
#   POST /voice/speak          — TTS only
#   GET  /rag/search           — test RAG retrieval
#   GET  /crm/{session_id}     — view student profile
#   GET  /tools/list           — list available tools
#   POST /tools/run            — run a tool directly
#   POST /reset/{session_id}   — reset session
# ─────────────────────────────────────────────

import uuid
import json
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from conversation import handle_turn
from session import clear_session, get_session_count
from llm import stream_response
from asr import transcribe_audio
from tts import text_to_speech, clean_text_for_speech
from rag import retrieve, format_context, collection
from crm import get_or_create_user, format_user_context
from tools import detect_tool, run_tool, TOOLS

# ── APP SETUP ─────────────────────────────────
app = FastAPI(title="AcadAI — University Advisor (RAG + Tools Edition)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── HEALTH CHECK ──────────────────────────────
# Shows status of all system components
# ─────────────────────────────────────────────
@app.get("/health")
async def health():
    """
    Returns status of all system components.
    Use this to verify everything is running.
    """
    return {
        "status":          "ok",
        "active_sessions": get_session_count(),
        "rag": {
            "status": "ok",
            "chunks": collection.count(),
        },
        "tools": list(TOOLS.keys()),
        "voice": "enabled"
    }


# ── WEBSOCKET TEXT CHAT ───────────────────────
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Main text chat endpoint.
    Handles full pipeline:
    policy → CRM → tools → scope → RAG → LLM → memory
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload      = json.loads(data)
                user_message = payload.get("message", "").strip()
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type":    "error",
                    "content": "Invalid message format."
                }))
                continue

            if not user_message:
                continue

            await websocket.send_text(json.dumps({"type": "start"}))

            full_reply = ""
            async for token in handle_turn(
                session_id    = session_id,
                user_message  = user_message,
                llm_stream_fn = stream_response
            ):
                if token == "__CONVERSATION_ENDED__":
                    await websocket.send_text(json.dumps({
                        "type":    "token",
                        "content": token
                    }))
                    continue

                full_reply += token
                await websocket.send_text(json.dumps({
                    "type":    "token",
                    "content": token
                }))

            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected.")


# ── WEBSOCKET VOICE ───────────────────────────
@app.websocket("/ws/voice")
async def websocket_voice(websocket: WebSocket):
    """
    Full voice pipeline:
    audio → ASR → conversation manager → TTS → audio
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"Voice session started: {session_id}")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()

            # STEP 1: ASR
            await websocket.send_text(json.dumps({
                "type": "status", "content": "Transcribing..."
            }))

            try:
                user_text = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, transcribe_audio, audio_bytes
                    ),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "type":    "error",
                    "content": "Transcription timed out. Please try again."
                }))
                continue

            if not user_text:
                await websocket.send_text(json.dumps({
                    "type":    "error",
                    "content": "Could not understand audio. Please try again."
                }))
                continue

            await websocket.send_text(json.dumps({
                "type": "transcription", "content": user_text
            }))

            # STEP 2: LLM via conversation manager
            await websocket.send_text(json.dumps({
                "type": "status", "content": "Thinking..."
            }))

            full_reply = ""
            async for token in handle_turn(
                session_id    = session_id,
                user_message  = user_text,
                llm_stream_fn = stream_response
            ):
                if token == "__CONVERSATION_ENDED__":
                    await websocket.send_text(json.dumps({
                        "type": "token", "content": token
                    }))
                    continue

                full_reply += token
                await websocket.send_text(json.dumps({
                    "type": "token", "content": token
                }))

            # STEP 3: TTS
            await websocket.send_text(json.dumps({
                "type": "status", "content": "Speaking..."
            }))

            clean_reply = clean_text_for_speech(full_reply)

            try:
                audio_response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, text_to_speech, clean_reply
                    ),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                audio_response = b""

            if audio_response:
                audio_b64 = base64.b64encode(audio_response).decode("utf-8")
                await websocket.send_text(json.dumps({
                    "type": "audio", "content": audio_b64
                }))

            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        print(f"Voice session {session_id} disconnected.")


# ── RAG SEARCH ENDPOINT ───────────────────────
# Test RAG retrieval independently
# Use in Postman: GET /rag/search?query=your question
# ─────────────────────────────────────────────
@app.get("/rag/search")
async def rag_search(query: str, top_k: int = 3):
    """
    Tests RAG retrieval directly.
    Returns top-k most relevant document chunks.

    Example: GET /rag/search?query=how to study for exams
    """
    if not query:
        return {"error": "Please provide a query parameter"}

    chunks = retrieve(query, top_k=top_k)

    return {
        "query":   query,
        "top_k":   top_k,
        "results": [
            {
                "rank":   i + 1,
                "source": chunk["source"],
                "score":  chunk["score"],
                "text":   chunk["text"][:200] + "..."
            }
            for i, chunk in enumerate(chunks)
        ]
    }


# ── CRM ENDPOINT ──────────────────────────────
# View student profile stored in CRM
# ─────────────────────────────────────────────
@app.get("/crm/{session_id}")
async def get_crm_profile(session_id: str):
    """
    Returns the CRM profile for a student session.
    Useful for debugging and Postman testing.

    Example: GET /crm/abc-123
    """
    user = get_or_create_user(session_id)
    return {
        "session_id":  session_id,
        "profile":     user,
        "context":     format_user_context(user)
    }


# ── TOOLS ENDPOINTS ───────────────────────────
@app.get("/tools/list")
async def list_tools():
    """
    Lists all available tools with descriptions.
    """
    return {
        "tools": [
            {
                "name":        name,
                "description": info["description"],
                "keywords":    info["keywords"][:5]
            }
            for name, info in TOOLS.items()
        ]
    }


@app.post("/tools/run")
async def run_tool_endpoint(payload: dict):
    """
    Runs a tool directly.
    Use in Postman to test tools independently.

    Body: {"tool": "calculator", "message": "calculate 15% of 200"}
    """
    tool_name = payload.get("tool", "")
    message   = payload.get("message", "")

    if not tool_name or not message:
        return {"error": "Provide 'tool' and 'message' in request body"}

    if tool_name not in TOOLS:
        return {
            "error":           f"Unknown tool: {tool_name}",
            "available_tools": list(TOOLS.keys())
        }

    result = await run_tool(tool_name, message)
    return {
        "tool":    tool_name,
        "message": message,
        "result":  result
    }


# ── VOICE ENDPOINTS ───────────────────────────
@app.post("/voice/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Test ASR independently — upload audio file."""
    audio_bytes = await file.read()
    text        = transcribe_audio(audio_bytes)
    return {"transcription": text}


@app.post("/voice/speak")
async def speak(payload: dict):
    """Test TTS independently — send text, get audio."""
    text = payload.get("text", "")
    if not text:
        return {"error": "No text provided"}

    clean       = clean_text_for_speech(text)
    audio_bytes = text_to_speech(clean)

    return Response(
        content     = audio_bytes,
        media_type  = "audio/wav",
        headers     = {"Content-Disposition": "attachment; filename=response.wav"}
    )


# ── RESET SESSION ─────────────────────────────
@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Resets conversation memory for a session."""
    clear_session(session_id)
    return {"status": "session cleared", "session_id": session_id}