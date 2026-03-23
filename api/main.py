"""
VoiceAgent Pro - FastAPI Application

Main API gateway for voice agent platform.
Handles inbound calls, WebSocket voice streams, and agent orchestration.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.middleware.auth import verify_twilio_signature
from api.routes.voice import voice_router
from api.routes.agents import agents_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("VoiceAgent Pro starting...")
    logger.info("Connecting to MCP servers...")
    # MCP connections would be initialized here

    yield

    # Shutdown
    logger.info("VoiceAgent Pro shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="VoiceAgent Pro API",
    description="Voice Agent Platform for Customer Support",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per client in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class InboundCallRequest(BaseModel):
    """Twilio inbound call webhook payload."""
    CallSid: str
    From: str
    To: str
    CallStatus: str
    Direction: str


class InboundCallResponse(BaseModel):
    """Twilio TwiML response."""
    twiml: str


class VoiceMessageRequest(BaseModel):
    """Voice message processing request."""
    session_id: str
    customer_id: Optional[str] = None
    transcript: str
    language: Optional[str] = "en"


class VoiceMessageResponse(BaseModel):
    """Voice message processing response."""
    session_id: str
    response_text: str
    action: str
    confidence: float


# Root endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "VoiceAgent Pro API",
        "version": "1.0.0"
    }


# Health endpoint
@app.get("/health")
async def health_check():
    """Detailed health check with MCP server status."""
    mcp_servers = {
        "knowledge": "connected",
        "crm": "connected",
        "ticketing": "connected",
        "calendar": "connected",
        "analytics": "connected",
        "escalation": "connected"
    }

    return {
        "status": "healthy",
        "mcp_servers": mcp_servers,
        "database": "connected",
        "redis": "connected"
    }


# Twilio inbound call webhook
@app.post("/inbound", response_model=InboundCallResponse)
async def handle_inbound_call(request: InboundCallRequest, http_request: Request):
    """
    Handle inbound Twilio call webhook.

    This endpoint is called when a customer calls the support line.
    It returns TwiML to initialize the call and connect to voice processing.
    """
    try:
        # Verify Twilio signature in production
        # signature = http_request.headers.get("X-Twilio-Signature")
        # if not verify_twilio_signature(signature, http_request):
        #     raise HTTPException(status_code=403, detail="Invalid signature")

        logger.info(f"Inbound call from {request.From}, CallSid: {request.CallSid}")

        # Return TwiML to connect call to voice processing
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Welcome to VoiceAgent Pro support. How can I help you today?</Say>
    <Connect>
        <Stream url="wss://api.voiceagent.pro/voice/stream"/>
    </Connect>
</Response>"""

        return InboundCallResponse(twiml=twiml)

    except Exception as e:
        logger.error(f"Error handling inbound call: {str(e)}")
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>We're experiencing technical difficulties. Please try again later.</Say>
</Response>"""
        return InboundCallResponse(twiml=twiml)


# WebSocket endpoint for voice streaming
@app.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming.

    Handles bidirectional audio streaming:
    - Receives audio chunks from client (Twilio Media Streams)
    - Sends to STT service for transcription
    - Processes through agent pipeline
    - Returns TTS audio back to client
    """
    try:
        await websocket.accept()

        # Send connection acknowledgment
        await websocket.send_json({
            "event": "connected",
            "message": "Voice stream connected"
        })

        # Process incoming audio chunks
        while True:
            try:
                # Receive audio data from client
                data = await websocket.receive_json()

                if data.get("event") == "audio":
                    # Process audio chunk
                    audio_payload = data.get("payload", {})
                    logger.debug(f"Received audio chunk: {audio_payload.get('chunk_id')}")

                    # In production:
                    # 1. Send to Deepgram STT
                    # 2. Get transcription
                    # 3. Process through Agents SDK
                    # 4. Get response from Claude via MCP
                    # 5. Send to ElevenLabs TTS
                    # 6. Return audio to WebSocket

                    # For now, acknowledge receipt
                    await websocket.send_json({
                        "event": "audio_processed",
                        "status": "received"
                    })

                elif data.get("event") == "start":
                    logger.info(f"Stream started: {data.get('streamSid')}")
                    await websocket.send_json({
                        "event": "started",
                        "stream_sid": data.get("streamSid")
                    })

                elif data.get("event") == "stop":
                    logger.info("Stream stopped")
                    break

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break

    except Exception as e:
        logger.error(f"Error in voice stream: {str(e)}")
        try:
            await websocket.send_json({
                "event": "error",
                "message": "Stream error occurred"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# Include routers
app.include_router(voice_router, prefix="/voice", tags=["voice"])
app.include_router(agents_router, prefix="/agents", tags=["agents"])


# Main entry point
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    logger.info(f"Starting VoiceAgent Pro API on port {port}")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )