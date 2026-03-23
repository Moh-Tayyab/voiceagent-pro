"""
Triage Agent - Entry point for all customer interactions

Built with OpenAI Agents SDK. Detects intent, language, and routes
to specialist agents.
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

from agents import Agent, Runner
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Supported intents for triage."""
    FAQ = "faq"
    BILLING = "billing"
    BOOKING = "booking"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"
    GENERAL = "general"


class TriageResult(BaseModel):
    """Structured triage output."""
    intent: Intent
    language: str
    confidence: float
    routed_to: str
    summary: str


# Urdu script character range: U+0600 to U+06FF
URDU_CHAR_RANGE = range(0x0600, 0x06FF)

# Words unique to each language (to avoid false matches)
URDU_ONLY = [
    "galat", "hunda", "mujhe", "tumhe", "apko", "karna", "chahta", "lekin",
    "phir", "toh", "mein", "ap", "hum", "hai", "tha", "kab", "kya"
]
ENGLISH_ONLY = [
    "the", "a", "an", "was", "were", "have", "has", "had", "will", "would",
    "could", "should", "reschedule"
]


def detect_language(text: str) -> str:
    """
    Detect language from input text.

    Uses script detection for Urdu (U+0600-U+06FF) and keyword matching
    for Roman Urdu. Language-specific keywords prevent false positives.
    """
    # Check for Urdu script characters
    for char in text:
        if ord(char) in URDU_CHAR_RANGE:
            return "ur"

    text_lower = text.lower()
    ur_score = sum(1 for w in URDU_ONLY if w in text_lower)
    en_score = sum(1 for w in ENGLISH_ONLY if w in text_lower)

    if ur_score > en_score and ur_score >= 1:
        return "ur"
    return "en"


# Intent keywords
INTENT_KEYWORDS = {
    Intent.FAQ: ["faq", "question", "how to", "what is", "policy", "information"],
    Intent.BILLING: ["billing", "payment", "refund", "charge", "invoice", "order", "cancel", "orders"],
    Intent.BOOKING: ["appointment", "booking", "schedule", "book", "meeting", "demo", "reschedule"],
    Intent.COMPLAINT: ["complaint", "issue", "problem", "not working", "broken", "wrong", "galat"],
    Intent.ESCALATION: ["escalate", "manager", "supervisor", "speak to human", "agent", "human"]
}


def detect_intent(text: str) -> tuple[Intent, float]:
    """
    Detect intent from input text.

    Returns intent and confidence score.
    """
    text_lower = text.lower()

    intent_scores = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        intent_scores[intent] = score

    # Find highest scoring intent
    if not any(intent_scores.values()):
        return Intent.GENERAL, 0.5

    max_intent = max(intent_scores, key=intent_scores.get)
    max_score = intent_scores[max_intent]

    # Normalize confidence (max 3 keywords typically match)
    confidence = min(max_score / 3.0, 1.0)

    return max_intent, confidence


def get_routing_target(intent: Intent) -> str:
    """
    Map intent to specialist agent.
    """
    routing_map = {
        Intent.FAQ: "faq_agent",
        Intent.BILLING: "billing_agent",
        Intent.BOOKING: "booking_agent",
        Intent.COMPLAINT: "billing_agent",  # Complaints often billing-related
        Intent.ESCALATION: "escalation_agent",
        Intent.GENERAL: "faq_agent"  # Default to FAQ for general queries
    }
    return routing_map.get(intent, "faq_agent")


# Triage Agent definition using OpenAI Agents SDK
# Note: Routing is handled in triage_message() via get_routing_target()
# to avoid circular imports with specialized agents
triage_agent = Agent(
    name="Triage Agent",
    instructions="""You are a customer support triage agent. Your job is to:
1. Understand the customer's query
2. Detect the language (English or Urdu)
3. Classify the intent (FAQ, billing, booking, complaint, escalation)
4. Route to the appropriate specialist agent

Keep responses brief and conversational. Always respond in the same language as the customer.

Routing rules:
- FAQ: General questions, policy information
- BILLING: Order status, refunds, payments, invoices
- BOOKING: Appointments, scheduling, demos
- COMPLAINT: Issues, problems, complaints
- ESCALATION: Customer requests human agent, unresolved issues""",
)


async def triage_message(
    message: str,
    session_id: str,
    customer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a message through the triage agent.

    Args:
        message: Customer message text
        session_id: Unique session identifier
        customer_id: Optional customer ID

    Returns:
        Dict with triage results and routing info
    """
    try:
        logger.info(f"Triage processing session={session_id}")

        # Detect language and intent
        language = detect_language(message)
        intent, confidence = detect_intent(message)
        routed_to = get_routing_target(intent)

        # Build triage result
        result = {
            "session_id": session_id,
            "customer_id": customer_id,
            "original_message": message,
            "language": language,
            "intent": intent.value,
            "confidence": round(confidence, 2),
            "routed_to": routed_to,
            "requires_handoff": confidence > 0.6
        }

        logger.info(f"Triage complete: intent={intent}, language={language}, route={routed_to}")

        return result

    except Exception as e:
        logger.error(f"Triage error: {str(e)}")
        return {
            "session_id": session_id,
            "error": str(e),
            "language": "en",
            "intent": "general",
            "routed_to": "faq_agent",
            "confidence": 0.5
        }


async def run_triage_agent(
    message: str,
    context: Optional[list] = None
) -> str:
    """
    Run the triage agent using OpenAI Agents SDK.

    This is the full agent execution with handoff support.
    """
    try:
        # Build initial context
        conversation_history = context or []
        conversation_history.append({"role": "user", "content": message})

        # Run the agent
        result = await Runner.run(
            triage_agent,
            conversation_history
        )

        return result.final_output

    except Exception as e:
        logger.error(f"Triage agent run error: {str(e)}")
        return "I apologize, but I'm having trouble understanding your request. Let me connect you with a specialist who can help."


# Voice response templates for triage
TRIAGE_RESPONSES = {
    "en": {
        Intent.FAQ: "I can help answer that question. Let me look that up for you.",
        Intent.BILLING: "I'll check your billing information right away.",
        Intent.BOOKING: "I'd be happy to help you schedule an appointment.",
        Intent.COMPLAINT: "I understand there's an issue. Let me look into this for you.",
        Intent.ESCALATION: "I'll connect you with a specialist who can assist further.",
        Intent.GENERAL: "Let me help you with that. Could you provide a bit more detail?"
    },
    "ur": {
        Intent.FAQ: "Main ap ka sawal samajh gaya hoon. Main ap ko madad karta hoon.",
        Intent.BILLING: "Main ap ki billing information abhi check karta hoon.",
        Intent.BOOKING: "Main ap ko appointment schedule karne mein madad kar sakta hoon.",
        Intent.COMPLAINT: "Main samajh gaya ke masla hai. Main isay check karta hoon.",
        Intent.ESCALATION: "Main ap ko specialist se connect kar deta hoon.",
        Intent.GENERAL: "Main ap ki madad karna chahta hoon. Thori aur tafseel batayen?"
    }
}


def get_triage_response(intent: Intent, language: str) -> str:
    """
    Get appropriate triage response in the customer's language.
    """
    lang_responses = TRIAGE_RESPONSES.get(language, TRIAGE_RESPONSES["en"])
    return lang_responses.get(intent, lang_responses[Intent.GENERAL])