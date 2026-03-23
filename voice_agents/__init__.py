"""
VoiceAgent Pro - Agents package

OpenAI Agents SDK agents for customer support.
"""

from voice_agents.triage_agent import triage_agent, triage_message
from voice_agents.faq_agent import faq_agent, process_faq_query
from voice_agents.billing_agent import billing_agent, process_billing_query
from voice_agents.booking_agent import booking_agent, process_booking_request
from voice_agents.escalation_agent import escalation_agent, process_escalation

__all__ = [
    "triage_agent",
    "faq_agent",
    "billing_agent",
    "booking_agent",
    "escalation_agent",
    "triage_message",
    "process_faq_query",
    "process_billing_query",
    "process_booking_request",
    "process_escalation"
]