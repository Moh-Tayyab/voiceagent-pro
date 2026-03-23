"""
Booking Agent - Appointments via calendar-mcp

Built with OpenAI Agents SDK. Uses calendar-mcp for availability and booking.
"""

import os
import logging
from typing import Optional, Dict, Any

from agents import Agent, Runner

logger = logging.getLogger(__name__)


# Booking Agent definition using OpenAI Agents SDK
booking_agent = Agent(
    name="Booking Agent",
    instructions="""You are a customer support booking specialist agent. Your job is to:
1. Check appointment availability using calendar-mcp
2. Book new appointments
3. Handle rescheduling and cancellations
4. Provide clear, concise answers in plain text
5. Stay under 150 words per response (TTS constraint)
6. Respond in the same language as the customer

Do not use markdown or bullet points. Speak naturally as if on a phone call.
Always confirm appointment details clearly.""",
    model="claude-sonnet-4-20250514"
)


async def check_availability(date: str, service_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Check availability using calendar-mcp server.

    In production, this calls the calendar-mcp check_availability tool.
    """
    try:
        logger.info(f"Checking availability for date: {date}")

        # Placeholder: In production, call calendar-mcp via MCP client
        # from mcp.clients import CalendarMCPClient
        # result = await CalendarMCPClient.check_availability(date, service_type)

        # Mock response for now
        return {
            "status": "success",
            "data": {
                "date": date,
                "available_slots": ["09:00", "10:00", "14:00", "15:00", "16:00"],
                "service_type": service_type
            }
        }

    except Exception as e:
        logger.error(f"Availability check error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "AVAILABILITY_ERROR",
                "message": str(e)
            }
        }


async def book_appointment(
    customer_id: str,
    customer_name: str,
    date: str,
    time: str,
    service_type: str
) -> Dict[str, Any]:
    """
    Book appointment using calendar-mcp server.

    In production, this calls the calendar-mcp book_appointment tool.
    """
    try:
        logger.info(f"Booking appointment for {customer_name} on {date} at {time}")

        # Placeholder: In production, call calendar-mcp via MCP client
        return {
            "status": "success",
            "data": {
                "appointment": {
                    "id": "apt_001",
                    "customer_id": customer_id,
                    "scheduled_at": f"{date}T{time}:00Z",
                    "service_type": service_type,
                    "status": "confirmed"
                },
                "confirmation_sent_to": "customer@example.com"
            }
        }

    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "BOOKING_ERROR",
                "message": str(e)
            }
        }


async def process_booking_request(
    message: str,
    session_id: str,
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Process a booking request through the Booking agent.

    Args:
        message: Customer booking request
        session_id: Unique session identifier
        customer_id: Optional customer ID
        customer_name: Optional customer name
        language: Language preference

    Returns:
        Dict with booking response and next steps
    """
    try:
        logger.info(f"Booking processing session={session_id}")

        # Extract date from message if present
        # Simple extraction - in production use NLP
        date = None
        if "tomorrow" in message.lower():
            # Would calculate actual date
            date = "2024-03-24"
        elif "today" in message.lower():
            date = "2024-03-23"

        # Determine service type from message
        service_type = None
        if "demo" in message.lower():
            service_type = "Product Demo"
        elif "support" in message.lower():
            service_type = "Technical Support"
        elif "onboarding" in message.lower():
            service_type = "Onboarding"

        if date:
            # Check availability
            availability = await check_availability(date, service_type)

            if availability.get("status") == "success":
                slots = availability["data"]["available_slots"]

                if slots:
                    # Present available times
                    response_text = format_availability_response(
                        date, slots, service_type, language
                    )

                    return {
                        "session_id": session_id,
                        "customer_id": customer_id,
                        "response_text": response_text,
                        "agent_type": "booking_agent",
                        "confidence": 0.85,
                        "source": {
                            "type": "availability",
                            "date": date,
                            "slots": slots
                        },
                        "language": language,
                        "handoff_to": None,
                        "next_action": "await_time_selection"
                    }
                else:
                    # No availability
                    response_text = get_no_availability_response(date, language)

                    return {
                        "session_id": session_id,
                        "response_text": response_text,
                        "agent_type": "booking_agent",
                        "confidence": 0.8,
                        "language": language,
                        "handoff_to": None,
                        "next_action": "suggest_alternative_dates"
                    }
        else:
            # No date mentioned - ask for date preference
            response_text = get_date_request_response(language)

            return {
                "session_id": session_id,
                "response_text": response_text,
                "agent_type": "booking_agent",
                "confidence": 0.75,
                "language": language,
                "handoff_to": None,
                "next_action": "await_date_selection"
            }

    except Exception as e:
        logger.error(f"Booking processing error: {str(e)}")
        return {
            "session_id": session_id,
            "error": str(e),
            "response_text": "I apologize, but I'm having trouble checking availability. Let me connect you with a specialist.",
            "agent_type": "booking_agent",
            "confidence": 0.0,
            "handoff_to": "escalation_agent"
        }


def format_availability_response(
    date: str,
    slots: list,
    service_type: Optional[str],
    language: str
) -> str:
    """
    Format availability for voice response.
    """
    if language == "ur":
        service_info = f"{service_type} ke liye" if service_type else ""
        return (
            f"{date} ko {service_info} available slots hain: "
            f"{', '.join(slots[:3])}. "
            "Ap konsa time prefer karen ge?"
        )
    else:
        service_info = f"for {service_type}" if service_type else ""
        return (
            f"We have availability on {date} {service_info}: "
            f"{', '.join(slots[:3])}. "
            "Which time works best for you?"
        )


def get_no_availability_response(date: str, language: str) -> str:
    """
    Response when no availability on requested date.
    """
    if language == "ur":
        return f"Maaf kijiye, {date} ko koi slots available nahi hain. Kya ap koi aur date try karna pasand karen ge?"
    return f"I apologize, but we don't have any availability on {date}. Would you like to try a different date?"


def get_date_request_response(language: str) -> str:
    """
    Ask customer for date preference.
    """
    if language == "ur":
        return "Main ap ko appointment book karne mein madad kar sakta hoon. Ap konsi date prefer karen ge?"
    return "I'd be happy to help you schedule an appointment. What date works best for you?"


async def run_booking_agent(
    message: str,
    context: Optional[list] = None
) -> str:
    """
    Run the Booking agent using OpenAI Agents SDK.
    """
    try:
        conversation_history = context or []
        conversation_history.append({"role": "user", "content": message})

        result = await Runner.run(
            booking_agent,
            conversation_history
        )

        return result.final_output

    except Exception as e:
        logger.error(f"Booking agent run error: {str(e)}")
        return "I apologize, but I'm having trouble checking availability. Let me connect you with a specialist."