"""
Agent Orchestration Service - Coordinates agents, MCP tools, and voice pipeline

Central service for processing voice messages through the agent hierarchy.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VoiceAgentOrchestrator:
    """
    Orchestrates voice message processing through agent hierarchy.

    Flow:
    1. Triage agent detects intent and language
    2. Routes to specialist agent (FAQ, Billing, Booking, Escalation)
    3. Specialist agent uses MCP tools for data lookup
    4. Response formatted for voice output
    5. Analytics logged
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.session_store = {}

    async def process_message(
        self,
        session_id: str,
        transcript: str,
        customer_id: Optional[str] = None,
        language: Optional[str] = "en",
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process a voice message through the agent pipeline.

        Args:
            session_id: Unique session identifier
            transcript: Transcribed text from STT
            customer_id: Optional customer ID
            language: Language preference
            context: Conversation history

        Returns:
            Dict with response text, agent info, and action
        """
        try:
            logger.info(f"Processing message session={session_id}")

            # Initialize session context
            if session_id not in self.session_store:
                self.session_store[session_id] = {
                    "created_at": datetime.utcnow().isoformat(),
                    "customer_id": customer_id,
                    "language": language,
                    "turn_count": 0,
                    "agent_history": [],
                    "context": context or []
                }

            session = self.session_store[session_id]
            session["turn_count"] += 1
            session["context"].append({"role": "user", "content": transcript})

            # Step 1: Triage
            triage_result = await self._run_triage(
                transcript, session_id, customer_id, language
            )

            session["agent_history"].append({
                "agent": "triage_agent",
                "intent": triage_result.get("intent"),
                "confidence": triage_result.get("confidence")
            })

            # Update language if detected differently
            if triage_result.get("language") != language:
                language = triage_result.get("language", "en")

            # Step 2: Route to specialist agent
            routed_to = triage_result.get("routed_to", "faq_agent")
            specialist_result = await self._run_specialist(
                routed_to,
                transcript,
                session_id,
                customer_id,
                language,
                session["context"]
            )

            session["agent_history"].append({
                "agent": routed_to,
                "response": specialist_result.get("response_text"),
                "confidence": specialist_result.get("confidence")
            })

            # Step 3: Check for handoff
            if specialist_result.get("handoff_to"):
                # Handle handoff
                handoff_result = await self._handle_handoff(
                    specialist_result["handoff_to"],
                    transcript,
                    session_id,
                    customer_id,
                    language,
                    session["context"]
                )
                session["agent_history"].append({
                    "agent": "handoff",
                    "to": handoff_result.get("to_agent")
                })

                return handoff_result

            # Step 4: Check for escalation
            if specialist_result.get("confidence", 1.0) < 0.6:
                # Low confidence - escalate
                escalation_result = await self._run_escalation(
                    transcript, session_id, customer_id, language,
                    "Low confidence on response"
                )
                return escalation_result

            # Step 5: Log analytics
            await self._log_analytics(
                session_id, customer_id, specialist_result, language
            )

            return specialist_result

        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            return {
                "session_id": session_id,
                "response_text": "I apologize, but I'm experiencing technical difficulties. Let me connect you with a specialist.",
                "agent_type": "error",
                "confidence": 0.0,
                "handoff_to": "escalation_agent"
            }

    async def _run_triage(
        self,
        message: str,
        session_id: str,
        customer_id: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Run triage agent."""
        from voice_agents.triage_agent import triage_message

        return await triage_message(message, session_id, customer_id)

    async def _run_specialist(
        self,
        agent_type: str,
        message: str,
        session_id: str,
        customer_id: Optional[str],
        language: str,
        context: list
    ) -> Dict[str, Any]:
        """Run specialist agent based on type."""
        if agent_type == "faq_agent":
            from voice_agents.faq_agent import process_faq_query
            return await process_faq_query(message, session_id, customer_id, language)

        elif agent_type == "billing_agent":
            from voice_agents.billing_agent import process_billing_query
            return await process_billing_query(message, session_id, customer_id, language)

        elif agent_type == "booking_agent":
            from voice_agents.booking_agent import process_booking_request
            return await process_booking_request(message, session_id, customer_id, language)

        elif agent_type == "escalation_agent":
            from voice_agents.escalation_agent import process_escalation
            return await process_escalation(message, session_id, customer_id, language=language)

        else:
            # Default to FAQ
            from voice_agents.faq_agent import process_faq_query
            return await process_faq_query(message, session_id, customer_id, language)

    async def _handle_handoff(
        self,
        to_agent: str,
        message: str,
        session_id: str,
        customer_id: Optional[str],
        language: str,
        context: list
    ) -> Dict[str, Any]:
        """Handle agent handoff."""
        logger.info(f"Handoff to {to_agent}")

        # Run target agent with context
        return await self._run_specialist(
            to_agent, message, session_id, customer_id, language, context
        )

    async def _run_escalation(
        self,
        message: str,
        session_id: str,
        customer_id: Optional[str],
        language: str,
        reason: str
    ) -> Dict[str, Any]:
        """Run escalation agent."""
        from voice_agents.escalation_agent import process_escalation

        return await process_escalation(
            message, session_id, customer_id, language=language,
            escalation_reason=reason
        )

    async def _log_analytics(
        self,
        session_id: str,
        customer_id: Optional[str],
        result: Dict[str, Any],
        language: str
    ):
        """Log call analytics."""
        # In production, call analytics-mcp
        # await analytics_mcp.log_call_outcome(...)
        logger.info(f"Analytics logged: session={session_id}, outcome=processed")


# Singleton instance
_orchestrator: Optional[VoiceAgentOrchestrator] = None


def get_orchestrator() -> VoiceAgentOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = VoiceAgentOrchestrator()
    return _orchestrator


# Convenience function
async def process_voice_message(
    session_id: str,
    transcript: str,
    customer_id: Optional[str] = None,
    language: Optional[str] = "en",
    context: Optional[list] = None
) -> Dict[str, Any]:
    """
    Process voice message through agent pipeline.

    Convenience function that uses the orchestrator singleton.
    """
    orchestrator = get_orchestrator()
    return await orchestrator.process_message(
        session_id, transcript, customer_id, language, context
    )