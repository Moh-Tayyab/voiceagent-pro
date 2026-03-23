"""
Twilio Routes - Inbound call webhooks and Media Streams handling

Handles Twilio webhook callbacks and voice stream connections.
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, WebSocket
from pydantic import BaseModel

from api.middleware.auth import verify_twilio_signature

logger = logging.getLogger(__name__)

# Router instance
twilio_router = APIRouter()


# Twilio webhook request model
class TwilioWebhookRequest(BaseModel):
    """Twilio inbound call webhook payload."""
    CallSid: str
    From: str
    To: str
    CallStatus: str
    Direction: str
    ApiVersion: Optional[str] = None


# TwiML response helper
def create_twilll_response(say: str = "", gather: Optional[dict] = None, connect: Optional[dict] = None) -> str:
    """
    Build TwiML response string.

    Args:
        say: Text to speak to caller
        gather: Gather settings (action, numDigits, etc.)
        connect: Connect settings for streaming

    Returns:
        TwiML XML string
    """
    twiml = '<?xml version="1.0" encoding="UTF-8"?>\n<Response>'

    if say:
        twiml += f'<Say>{say}</Say>'

    if gather:
        action = gather.get("action", "/voice/process")
        num_digits = gather.get("numDigits", 0)
        twiml += f'<Gather action="{action}" numDigits="{num_digits}">'

    if connect:
        stream_url = connect.get("url", "wss://api.voiceagent.pro/voice/stream")
        twiml += f'<Connect><Stream url="{stream_url}"/></Connect>'

    if gather:
        twiml += '</Gather>'

    twiml += '</Response>'

    return twiml


@twilio_router.post("/inbound")
async def handle_inbound_call(request: Request):
    """
    Handle Twilio inbound call webhook.

    This endpoint is called when a customer calls the support line.
    Returns TwiML to initialize the call and connect to voice processing.
    """
    try:
        # Parse form data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")

        logger.info(f"Inbound call: CallSid={call_sid}, From={from_number}, To={to_number}")

        # Verify Twilio signature in production
        # signature = request.headers.get("X-Twilio-Signature")
        # base_url = str(request.base_url) + "inbound"
        # if not verify_twilio_signature(signature, base_url, dict(form_data)):
        #     raise HTTPException(status_code=403, detail="Invalid signature")

        # Build TwiML response
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Welcome to VoiceAgent Pro support. How can I help you today?</Say>
    <Connect>
        <Stream url="wss://api.voiceagent.pro/voice/stream"/>
    </Connect>
</Response>"""

        return Response(
            content=twiml,
            media_type="application/xml"
        )

    except Exception as e:
        logger.error(f"Error handling inbound call: {str(e)}")

        # Fallback TwiML
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>We're experiencing technical difficulties. Please try again later.</Say>
</Response>"""

        return Response(
            content=twiml,
            media_type="application/xml"
        )


@twilio_router.post("/status")
async def handle_call_status(request: Request):
    """
    Handle Twilio call status callback.

    Called when call status changes (completed, busy, failed, etc.)
    Logs call outcome for analytics.
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        duration = form_data.get("Duration", 0)

        logger.info(f"Call status update: CallSid={call_sid}, Status={call_status}, Duration={duration}s")

        # In production, log to analytics-mcp
        # await analytics_mcp.log_call_outcome(
        #     session_id=call_sid,
        #     outcome=call_status,
        #     duration_seconds=int(duration) if duration else 0
        # )

        return {"status": "logged", "call_sid": call_sid}

    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}")
        return {"status": "error", "error": str(e)}


@twilio_router.websocket("/stream")
async def handle_media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.

    Handles bidirectional audio streaming:
    - Receives audio chunks from Twilio
    - Sends to Deepgram STT for transcription
    - Processes through agent pipeline
    - Returns TTS audio back to Twilio
    """
    try:
        await websocket.accept()

        # Send connection acknowledgment
        await websocket.send_json({
            "event": "connected",
            "message": "Media stream connected"
        })

        stream_sid = None
        call_sid = None

        # Process incoming media chunks
        while True:
            try:
                data = await websocket.receive_json()
                event = data.get("event")

                if event == "start":
                    stream_sid = data.get("streamSid")
                    call_sid = data.get("start", {}).get("callSid")
                    logger.info(f"Stream started: streamSid={stream_sid}, callSid={call_sid}")

                    # Send start acknowledgment
                    await websocket.send_json({
                        "event": "started",
                        "streamSid": stream_sid
                    })

                elif event == "media":
                    # Received audio chunk
                    media_payload = data.get("media", {})
                    audio_payload = media_payload.get("payload")

                    if audio_payload:
                        # In production:
                        # 1. Decode base64 audio
                        # 2. Send to Deepgram STT
                        # 3. Get transcription
                        # 4. Process through agent
                        # 5. Get response from Claude via MCP
                        # 6. Send to ElevenLabs TTS
                        # 7. Return audio to WebSocket

                        logger.debug(f"Received audio chunk: {media_payload.get('chunk_id')}")

                        # Acknowledge receipt (placeholder)
                        await websocket.send_json({
                            "event": "audio_processed",
                            "status": "received"
                        })

                elif event == "stop":
                    logger.info(f"Stream stopped: streamSid={stream_sid}")

                    # Log call completion
                    # await analytics_mcp.log_call_outcome(...)

                    break

                elif event == "close":
                    logger.info("Stream closed")
                    break

            except WebSocketDisconnect:
                logger.info("Twilio disconnected")
                break

    except Exception as e:
        logger.error(f"Error in media stream: {str(e)}")
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


@twilio_router.post("/message")
async def process_voice_message(
    session_id: str,
    transcript: str,
    customer_id: Optional[str] = None,
    language: Optional[str] = "en"
):
    """
    Process a transcribed voice message through the agent pipeline.

    This is called by the voice stream handler after STT processing.
    """
    try:
        from api.services.orchestration import process_voice_message

        result = await process_voice_message(
            session_id=session_id,
            transcript=transcript,
            customer_id=customer_id,
            language=language
        )

        return result

    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")