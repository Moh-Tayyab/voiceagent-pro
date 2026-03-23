---
name: fastapi-route-skill
description: FastAPI async route patterns with proper error handling, request validation, and OpenAPI schemas
---

# FastAPI Route Skill

Patterns for building FastAPI routes with async support.

## Async Route Pattern

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class InboundRequest(BaseModel):
    call_sid: str
    from_number: str
    transcription: str

class AgentResponse(BaseModel):
    response_text: str
    agent_type: str
    confidence: float

@app.post("/inbound")
async def handle_inbound(request: InboundRequest) -> AgentResponse:
    """Handle inbound call with transcription."""
    try:
        result = await process_call(request)
        return AgentResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Inbound error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Request/Response Models

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class CustomerInfo(BaseModel):
    customer_id: Optional[str] = None
    name: Optional[str] = None
    language: str = "en"

class InboundRequest(BaseModel):
    call_sid: str = Field(..., description="Twilio call SID")
    from_number: str = Field(..., description="Caller phone number")
    transcription: str = Field(..., description="Speech-to-text transcription")
    customer: Optional[CustomerInfo] = None

class OutboundRequest(BaseModel):
    to_number: str
    response_text: str
    voice_id: str = "default"

class OutboundResponse(BaseModel):
    status: str
    message_sid: Optional[str] = None
```

## Error Handling

```python
from fastapi import HTTPException, status

@app.post("/api/orders/{order_id}/cancel")
async def cancel_order(order_id: str) -> dict:
    try:
        result = await order_service.cancel(order_id)
        return {"status": "success", "data": result}
    except OrderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": f"Order {order_id} not found"}
        )
    except OrderAlreadyCancelledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_CANCELLED", "message": "Order is already cancelled"}
        )
    except Exception as e:
        logger.error(f"Cancel order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Failed to cancel order"}
        )
```

## Webhook Endpoints

```python
from fastapi import Header, Request
from typing import Optional

@app.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
) -> dict:
    """Handle Twilio status callbacks."""
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")

    await call_tracker.update_status(call_sid, call_status)

    return {"status": "received"}

@app.post("/webhook/deepgram")
async def deepgram_webhook(request: Request) -> dict:
    """Handle Deepgram transcription callbacks."""
    body = await request.json()
    transcription = body.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")

    if transcription:
        await message_queue.publish(transcription)

    return {"status": "processed"}
```

## Streaming Responses

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

@app.get("/stream/{session_id}")
async def stream_response(session_id: str):
    """Stream agent responses via SSE."""
    async def event_generator():
        async for chunk in agent_stream.get_messages(session_id):
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.01)  # Allow cancellation

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

## Health Check

```python
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": os.getenv("VERSION", "dev"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness check - verifies dependencies."""
    try:
        await db.ping()
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

## Running the Server

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,  # Use 1 worker in dev; gunicorn for production
    )
```

## Project Structure

```
api/
├── main.py           # FastAPI app, routes
├── models.py         # Pydantic models
├── routes/
│   ├── inbound.py    # Inbound call handling
│   ├── outbound.py   # Outbound call initiation
│   └── webhooks.py   # Webhook handlers
├── services/
│   ├── agent.py      # Agent orchestration
│   └── telephony.py  # Twilio integration
└── dependencies.py   # Shared dependencies
```
