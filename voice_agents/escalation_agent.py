"""
Escalation Agent - Routes to human, creates urgent ticket via escalation-mcp

Built with OpenAI Agents SDK. Uses escalation-mcp for routing to human agents.
"""

import os
import logging
from typing import Optional, Dict, Any

from agents import Agent, Runner

logger = logging.getLogger(__name__)


# Escalation Agent definition using OpenAI Agents SDK
escalation_agent = Agent(
    name="Escalation Agent",
    instructions="""You are a customer support escalation specialist agent. Your job is to:
1. Determine when escalation to a human agent is needed
2. Collect necessary context from the customer
3. Create urgent tickets via escalation-mcp
4. Route to appropriate human agent level
5. Provide clear, empathetic responses in plain text
6. Stay under 150 words per response (TTS constraint)

Escalation triggers:
- Customer explicitly requests human agent
- Issue unresolved after 2 turns
- Low confidence (< 0.6) on intent classification
- Complex billing disputes or technical issues
- Complaints about service quality

Always be empathetic and assure the customer that a specialist will help.""",
    model="claude-sonnet-4-20250514"
)


async def route_to_human(
    customer_id: str,
    reason: str,
    level: str = "l1",
    callback_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route to human agent using escalation-mcp server.

    In production, this calls the escalation-mcp route_to_human tool.
    """
    try:
        logger.info(f"Routing to human: customer={customer_id}, reason={reason}")

        # Placeholder: In production, call escalation-mcp via MCP client
        # from mcp.clients import EscalationMCPClient
        # result = await EscalationMCPClient.route_to_human(customer_id, reason, level, callback_number)

        # Mock response for now
        return {
            "status": "success",
            "data": {
                "escalation": {
                    "id": "esc_001",
                    "customer_id": customer_id,
                    "level": level,
                    "reason": reason,
                    "status": "pending",
                    "assigned_to": "agent_001"
                },
                "assigned_agent": {
                    "name": "Alice Johnson",
                    "phone": "+1-555-0201"
                },
                "estimated_callback": "within 30 minutes"
            }
        }

    except Exception as e:
        logger.error(f"Route to human error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ROUTE_ERROR",
                "message": str(e)
            }
        }


async def create_urgent_ticket(
    customer_id: str,
    subject: str,
    description: str,
    callback_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create urgent ticket using escalation-mcp server.

    In production, this calls the escalation-mcp create_urgent_ticket tool.
    """
    try:
        logger.info(f"Creating urgent ticket for customer: {customer_id}")

        # Placeholder: In production, call escalation-mcp via MCP client
        return {
            "status": "success",
            "data": {
                "ticket": {
                    "id": "tkt_urgent_001",
                    "customer_id": customer_id,
                    "subject": subject,
                    "priority": "urgent",
                    "requires_callback": True
                }
            }
        }

    except Exception as e:
        logger.error(f"Urgent ticket error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "TICKET_ERROR",
                "message": str(e)
            }
        }


async def process_escalation(
    message: str,
    session_id: str,
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    language: str = "en",
    escalation_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an escalation request through the Escalation agent.

    Args:
        message: Customer message
        session_id: Unique session identifier
        customer_id: Optional customer ID
        customer_name: Optional customer name
        language: Language preference
        escalation_reason: Reason for escalation

    Returns:
        Dict with escalation response and routing info
    """
    try:
        logger.info(f"Escalation processing session={session_id}")

        # Determine escalation reason if not provided
        if not escalation_reason:
            if "human" in message.lower() or "agent" in message.lower():
                escalation_reason = "Customer requested human agent"
            elif "complaint" in message.lower():
                escalation_reason = "Customer complaint requiring specialist review"
            else:
                escalation_reason = "Complex issue requiring specialist assistance"

        # Extract callback number if present (simple extraction)
        callback_number = None
        # In production, use proper phone number extraction

        # Route to human agent
        route_result = await route_to_human(
            customer_id or "unknown",
            escalation_reason,
            level="l1",
            callback_number=callback_number
        )

        if route_result.get("status") == "success":
            assigned_agent = route_result["data"]["assigned_agent"]
            estimated_callback = route_result["data"]["estimated_callback"]

            response_text = format_escalation_response(
                assigned_agent["name"],
                estimated_callback,
                language
            )

            return {
                "session_id": session_id,
                "customer_id": customer_id,
                "response_text": response_text,
                "agent_type": "escalation_agent",
                "confidence": 0.95,
                "source": {
                    "type": "escalation",
                    "escalation_id": route_result["data"]["escalation"]["id"],
                    "assigned_to": assigned_agent["name"]
                },
                "language": language,
                "handoff_to": None,
                "escalation_completed": True,
                "assigned_agent": assigned_agent["name"],
                "estimated_callback": estimated_callback
            }
        else:
            # Escalation failed
            response_text = get_escalation_fallback_response(language)

            return {
                "session_id": session_id,
                "response_text": response_text,
                "agent_type": "escalation_agent",
                "confidence": 0.5,
                "language": language,
                "handoff_to": None,
                "escalation_completed": False
            }

    except Exception as e:
        logger.error(f"Escalation processing error: {str(e)}")
        return {
            "session_id": session_id,
            "error": str(e),
            "response_text": "I apologize for the inconvenience. Please call back later and ask for a supervisor.",
            "agent_type": "escalation_agent",
            "confidence": 0.0,
            "escalation_completed": False
        }


def format_escalation_response(
    agent_name: str,
    estimated_callback: str,
    language: str
) -> str:
    """
    Format escalation confirmation for voice response.
    """
    if language == "ur":
        return (
            f"Main ap ko {agent_name} se connect kar raha hoon. "
            f"Woh {estimated_callback} mein ap se contact karen gi. "
            "Kya main aur kuch madad kar sakta hoon?"
        )
    else:
        return (
            f"I'm connecting you with {agent_name}. "
            f"They will contact you {estimated_callback}. "
            "Is there anything else I can help you with?"
        )


def get_escalation_fallback_response(language: str) -> str:
    """
    Fallback response when escalation fails.
    """
    if language == "ur":
        return "Maaf kijiye, main abhi kisi agent ko connect nahi kar sakta. Barah meherbani baad mein call karen."
    return "I apologize, but I'm unable to connect you with an agent right now. Please call back later."


async def run_escalation_agent(
    message: str,
    context: Optional[list] = None
) -> str:
    """
    Run the Escalation agent using OpenAI Agents SDK.
    """
    try:
        conversation_history = context or []
        conversation_history.append({"role": "user", "content": message})

        result = await Runner.run(
            escalation_agent,
            conversation_history
        )

        return result.final_output

    except Exception as e:
        logger.error(f"Escalation agent run error: {str(e)}")
        return get_escalation_fallback_response("en")