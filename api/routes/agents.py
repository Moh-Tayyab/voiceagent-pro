"""
Agents Routes - Agent orchestration and handoff endpoints
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Router instance
agents_router = APIRouter()


# Request/Response Models
class AgentRequest(BaseModel):
    """Agent processing request."""
    session_id: str
    customer_id: Optional[str] = None
    message: str
    context: Optional[dict] = None
    language: Optional[str] = "en"


class AgentResponse(BaseModel):
    """Agent processing response."""
    session_id: str
    response_text: str
    agent_type: str
    confidence: float
    handoff_to: Optional[str] = None
    action_required: Optional[str] = None


class HandoffRequest(BaseModel):
    """Agent handoff request."""
    session_id: str
    from_agent: str
    to_agent: str
    context: dict


@agents_router.post("/triage", response_model=AgentResponse)
async def triage_message(request: AgentRequest):
    """
    Process message through triage agent.

    The triage agent is the entry point that:
    - Detects intent (FAQ, billing, booking, complaint, escalation)
    - Detects language preference
    - Routes to appropriate specialist agent
    """
    try:
        logger.info(f"Triage processing for session: {request.session_id}")

        # Placeholder: In production, call Triage Agent
        # from agents.triage_agent import triage
        # result = await triage(request)

        # Mock triage response
        response = AgentResponse(
            session_id=request.session_id,
            response_text="I understand. Let me connect you with the right specialist.",
            agent_type="triage_agent",
            confidence=0.90,
            handoff_to="faq_agent",
            action_required=None
        )

        return response

    except Exception as e:
        logger.error(f"Triage error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")


@agents_router.post("/faq", response_model=AgentResponse)
async def faq_query(request: AgentRequest):
    """
    Process FAQ query through FAQ agent.

    Uses knowledge-mcp to search FAQs and policies.
    """
    try:
        logger.info(f"FAQ processing for session: {request.session_id}")

        # Placeholder: In production, call FAQ Agent with knowledge-mcp
        # from agents.faq_agent import answer_faq
        # result = await answer_faq(request)

        response = AgentResponse(
            session_id=request.session_id,
            response_text="I found information about that in our FAQs.",
            agent_type="faq_agent",
            confidence=0.85,
            handoff_to=None,
            action_required="display_faq"
        )

        return response

    except Exception as e:
        logger.error(f"FAQ error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"FAQ processing failed: {str(e)}")


@agents_router.post("/billing", response_model=AgentResponse)
async def billing_query(request: AgentRequest):
    """
    Process billing query through Billing agent.

    Uses crm-mcp to lookup customer and order history.
    """
    try:
        logger.info(f"Billing processing for session: {request.session_id}")

        response = AgentResponse(
            session_id=request.session_id,
            response_text="Let me look up your account and billing information.",
            agent_type="billing_agent",
            confidence=0.80,
            handoff_to=None,
            action_required="lookup_customer"
        )

        return response

    except Exception as e:
        logger.error(f"Billing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Billing processing failed: {str(e)}")


@agents_router.post("/booking", response_model=AgentResponse)
async def booking_request(request: AgentRequest):
    """
    Process appointment booking through Booking agent.

    Uses calendar-mcp to check availability and book appointments.
    """
    try:
        logger.info(f"Booking processing for session: {request.session_id}")

        response = AgentResponse(
            session_id=request.session_id,
            response_text="I can help you schedule an appointment. What date works for you?",
            agent_type="booking_agent",
            confidence=0.85,
            handoff_to=None,
            action_required="check_availability"
        )

        return response

    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Booking processing failed: {str(e)}")


@agents_router.post("/escalate", response_model=AgentResponse)
async def escalate_issue(request: AgentRequest):
    """
    Process escalation through Escalation agent.

    Uses escalation-mcp to route to human agent.
    """
    try:
        logger.info(f"Escalation processing for session: {request.session_id}")

        response = AgentResponse(
            session_id=request.session_id,
            response_text="I'm connecting you with a specialist who can help.",
            agent_type="escalation_agent",
            confidence=0.95,
            handoff_to=None,
            action_required="route_to_human"
        )

        return response

    except Exception as e:
        logger.error(f"Escalation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Escalation failed: {str(e)}")


@agents_router.post("/handoff")
async def handle_handoff(request: HandoffRequest):
    """
    Handle agent handoff with context transfer.

    Transfers conversation context from one agent to another.
    """
    try:
        logger.info(f"Handoff from {request.from_agent} to {request.to_agent}")

        # Validate handoff
        valid_agents = ["triage", "faq", "billing", "booking", "escalation"]
        if request.to_agent.lower() not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target agent: {request.to_agent}"
            )

        return {
            "status": "success",
            "session_id": request.session_id,
            "from_agent": request.from_agent,
            "to_agent": request.to_agent,
            "context_transferred": True,
            "message": f"Handoff to {request.to_agent} complete"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Handoff error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Handoff failed: {str(e)}")


@agents_router.get("/status/{session_id}")
async def get_agent_status(session_id: str):
    """Get current agent status for a session."""
    return {
        "session_id": session_id,
        "current_agent": "triage_agent",
        "status": "active",
        "language": "en",
        "turn_count": 1
    }