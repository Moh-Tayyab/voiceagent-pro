"""
Billing Agent - Order status, refunds, payment queries using crm-mcp

Built with OpenAI Agents SDK. Uses crm-mcp for customer lookup and order history.
"""

import os
import logging
from typing import Optional, Dict, Any

from agents import Agent, Runner

logger = logging.getLogger(__name__)


# Billing Agent definition using OpenAI Agents SDK
billing_agent = Agent(
    name="Billing Agent",
    instructions="""You are a customer support billing specialist agent. Your job is to:
1. Look up customer accounts using crm-mcp
2. Check order status and history
3. Handle refund and payment queries
4. Provide clear, concise answers in plain text
5. Stay under 150 words per response (TTS constraint)
6. Respond in the same language as the customer

Do not use markdown or bullet points. Speak naturally as if on a phone call.
For complex billing disputes, escalate to a human agent.""",
    model="claude-sonnet-4-20250514"
)


async def lookup_customer(identifier: str, identifier_type: str = "email") -> Dict[str, Any]:
    """
    Look up customer using crm-mcp server.

    In production, this calls the crm-mcp customer_lookup tool.
    """
    try:
        logger.info(f"Looking up customer by {identifier_type}: {identifier}")

        # Placeholder: In production, call crm-mcp via MCP client
        # from mcp.clients import CRMMCPClient
        # result = await CRMMCPClient.customer_lookup(identifier, identifier_type)

        # Mock response for now
        return {
            "status": "success",
            "data": {
                "customer": {
                    "id": "cust_001",
                    "name": "John Smith",
                    "email": identifier if identifier_type == "email" else "customer@example.com",
                    "tier": "premium"
                },
                "account": {
                    "balance": 0.00,
                    "status": "active"
                }
            }
        }

    except Exception as e:
        logger.error(f"Customer lookup error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "LOOKUP_ERROR",
                "message": str(e)
            }
        }


async def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Get order status using crm-mcp server.

    In production, this calls the crm-mcp get_order_status tool.
    """
    try:
        logger.info(f"Checking order status: {order_id}")

        # Placeholder: In production, call crm-mcp via MCP client
        return {
            "status": "success",
            "data": {
                "order": {
                    "id": order_id,
                    "status": "shipped",
                    "tracking_number": "TRK123456789",
                    "estimated_delivery": "2024-03-25"
                }
            }
        }

    except Exception as e:
        logger.error(f"Order status error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ORDER_ERROR",
                "message": str(e)
            }
        }


async def process_billing_query(
    message: str,
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Process a billing query through the Billing agent.

    Args:
        message: Customer question about billing/order
        session_id: Unique session identifier
        customer_id: Optional customer ID
        language: Language preference

    Returns:
        Dict with billing response and order info
    """
    try:
        logger.info(f"Billing processing session={session_id}")

        # If customer_id provided, look up their info
        if customer_id:
            customer_result = await lookup_customer(customer_id, "customer_id")

            if customer_result.get("status") == "success":
                customer_name = customer_result["data"]["customer"]["name"]
                greeting = f"Hello {customer_name}" if language == "en" else f"Salam {customer_name}"
            else:
                greeting = "Hello" if language == "en" else "Salam"
        else:
            greeting = "Hello" if language == "en" else "Salam"

        # Check if message contains order ID pattern
        order_id = None
        if "order" in message.lower() and "#" in message:
            parts = message.split("#")
            if len(parts) > 1:
                order_id = parts[1].split()[0]

        if order_id:
            # Check order status
            order_result = await get_order_status(order_id)

            if order_result.get("status") == "success":
                order_data = order_result["data"]["order"]
                response_text = format_order_response(order_data, language)

                return {
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "response_text": response_text,
                    "agent_type": "billing_agent",
                    "confidence": 0.9,
                    "source": {
                        "type": "order",
                        "order_id": order_id
                    },
                    "language": language,
                    "handoff_to": None
                }

        # General billing query - provide helpful response
        response_text = get_general_billing_response(language)

        return {
            "session_id": session_id,
            "customer_id": customer_id,
            "response_text": f"{greeting}. {response_text}",
            "agent_type": "billing_agent",
            "confidence": 0.7,
            "source": None,
            "language": language,
            "handoff_to": None
        }

    except Exception as e:
        logger.error(f"Billing processing error: {str(e)}")
        return {
            "session_id": session_id,
            "error": str(e),
            "response_text": "I apologize, but I'm having trouble accessing your account information. Let me connect you with a specialist.",
            "agent_type": "billing_agent",
            "confidence": 0.0,
            "handoff_to": "escalation_agent"
        }


def format_order_response(order_data: Dict[str, Any], language: str) -> str:
    """
    Format order data for voice response.
    """
    if language == "ur":
        return (
            f"Ap ka order {order_data.get('id')} {order_data.get('status')} hai. "
            f"Tracking number hai {order_data.get('tracking_number')}. "
            f"Delivery {order_data.get('estimated_delivery')} tak expected hai. "
            "Kya main aur kuch madad kar sakta hoon?"
        )
    else:
        return (
            f"Your order {order_data.get('id')} is {order_data.get('status')}. "
            f"Tracking number is {order_data.get('tracking_number')}. "
            f"Expected delivery is {order_data.get('estimated_delivery')}. "
            "Can I help you with anything else?"
        )


def get_general_billing_response(language: str) -> str:
    """
    Get general billing response when no specific order is mentioned.
    """
    if language == "ur":
        return "Main ap ki billing mein kaise madad kar sakta hoon? Kya ap kisi specific order ke baray mein pooch rahe hain?"
    return "How can I help you with your billing? Are you asking about a specific order?"


async def run_billing_agent(
    message: str,
    context: Optional[list] = None
) -> str:
    """
    Run the Billing agent using OpenAI Agents SDK.
    """
    try:
        conversation_history = context or []
        conversation_history.append({"role": "user", "content": message})

        result = await Runner.run(
            billing_agent,
            conversation_history
        )

        return result.final_output

    except Exception as e:
        logger.error(f"Billing agent run error: {str(e)}")
        return "I apologize, but I'm having trouble accessing your account information. Let me connect you with a specialist."