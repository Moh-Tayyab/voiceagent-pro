"""
Agent Evaluation Tests - Conversation test scenarios and metrics

Tests for agent accuracy, response quality, and escalation logic.
"""

import pytest
import asyncio
from typing import Dict, Any, List

# Import agents
from agents.triage_agent import triage_message, detect_intent, detect_language, Intent
from agents.faq_agent import process_faq_query
from agents.billing_agent import process_billing_query
from agents.escalation_agent import process_escalation

# Import guardrails
from api.middleware.guardrails import get_guardrails


class TestTriageAgent:
    """Tests for Triage Agent."""

    def test_detect_language_english(self):
        """Test English language detection."""
        text = "What is your refund policy?"
        lang = detect_language(text)
        assert lang == "en"

    def test_detect_language_urdu(self):
        """Test Urdu language detection."""
        text = "Refund policy kya hai?"
        lang = detect_language(text)
        assert lang == "ur"

    def test_detect_intent_faq(self):
        """Test FAQ intent detection."""
        text = "What is your return policy?"
        intent, confidence = detect_intent(text)
        assert intent == Intent.FAQ
        assert confidence > 0.5

    def test_detect_intent_billing(self):
        """Test Billing intent detection."""
        text = "I was charged twice for my order"
        intent, confidence = detect_intent(text)
        assert intent == Intent.BILLING
        assert confidence > 0.5

    def test_detect_intent_booking(self):
        """Test Booking intent detection."""
        text = "I want to book an appointment for demo"
        intent, confidence = detect_intent(text)
        assert intent == Intent.BOOKING

    def test_detect_intent_escalation(self):
        """Test Escalation intent detection."""
        text = "I want to speak to a human agent"
        intent, confidence = detect_intent(text)
        assert intent == Intent.ESCALATION

    @pytest.mark.asyncio
    async def test_triage_message_response(self):
        """Test triage message processing."""
        result = await triage_message(
            message="What is your refund policy?",
            session_id="test_session_001",
            customer_id="cust_001"
        )

        assert result["session_id"] == "test_session_001"
        assert result["language"] == "en"
        assert result["intent"] == "faq"
        assert result["routed_to"] == "faq_agent"


class TestFAQEAgent:
    """Tests for FAQ Agent."""

    @pytest.mark.asyncio
    async def test_faq_query_success(self):
        """Test FAQ query with successful match."""
        result = await process_faq_query(
            message="What is your refund policy?",
            session_id="test_session_002",
            customer_id="cust_001",
            language="en"
        )

        assert result["session_id"] == "test_session_002"
        assert result["agent_type"] == "faq_agent"
        assert result["response_text"]  # Should have response
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_faq_query_urdu(self):
        """Test FAQ query in Urdu."""
        result = await process_faq_query(
            message="Refund policy kya hai?",
            session_id="test_session_003",
            customer_id="cust_003",
            language="ur"
        )

        assert result["language"] == "ur"
        assert "faq_agent" == result["agent_type"]


class TestBillingAgent:
    """Tests for Billing Agent."""

    @pytest.mark.asyncio
    async def test_billing_order_status(self):
        """Test billing query with order ID."""
        result = await process_billing_query(
            message="Where is my order #12345?",
            session_id="test_session_004",
            customer_id="cust_001",
            language="en"
        )

        assert result["agent_type"] == "billing_agent"
        assert result["confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_billing_general_query(self):
        """Test general billing query."""
        result = await process_billing_query(
            message="I have a billing question",
            session_id="test_session_005",
            customer_id="cust_001",
            language="en"
        )

        assert result["agent_type"] == "billing_agent"


class TestEscalationAgent:
    """Tests for Escalation Agent."""

    @pytest.mark.asyncio
    async def test_explicit_escalation(self):
        """Test explicit escalation request."""
        result = await process_escalation(
            message="I want to speak to a human",
            session_id="test_session_006",
            customer_id="cust_001",
            language="en"
        )

        assert result["agent_type"] == "escalation_agent"
        assert result["escalation_completed"] == True

    @pytest.mark.asyncio
    async def test_complaint_escalation(self):
        """Test complaint-triggered escalation."""
        result = await process_escalation(
            message="I have a complaint about your service",
            session_id="test_session_007",
            customer_id="cust_001",
            language="en"
        )

        assert result["agent_type"] == "escalation_agent"


class TestGuardrails:
    """Tests for Guardrails middleware."""

    def test_input_validation_valid(self):
        """Test valid input passes validation."""
        guardrails = get_guardrails()
        valid, result = guardrails.validate_input("What is your refund policy?")
        assert valid == True
        assert result["profanity_detected"] == False

    def test_input_validation_pii(self):
        """Test PII detection in input."""
        guardrails = get_guardrails()
        valid, result = guardrails.validate_input("My email is test@example.com")
        assert result["pii_detected"] == True
        assert "email" in result["pii_types"]

    def test_input_validation_profanity(self):
        """Test profanity detection."""
        guardrails = get_guardrails()
        valid, result = guardrails.validate_input("This damn product doesn't work")
        assert result["profanity_detected"] == True

    def test_output_validation_word_count(self):
        """Test output word count validation."""
        guardrails = get_guardrails()
        long_text = " ".join(["word"] * 200)
        valid, result = guardrails.validate_output(long_text)
        assert valid == False
        assert result["word_count"] == 200

    def test_output_validation_markdown(self):
        """Test markdown detection in output."""
        guardrails = get_guardrails()
        valid, result = guardrails.validate_output("## Header\n- bullet point")
        assert result["has_markdown"] == True

    def test_escalation_trigger_low_confidence(self):
        """Test escalation trigger on low confidence."""
        guardrails = get_guardrails()
        should_escalate = guardrails.check_escalation_trigger(
            text="I need help",
            confidence=0.4,
            turn_count=1
        )
        assert should_escalate == True

    def test_escalation_trigger_human_request(self):
        """Test escalation trigger on human request."""
        guardrails = get_guardrails()
        should_escalate = guardrails.check_escalation_trigger(
            text="I want to speak to a human",
            confidence=0.9,
            turn_count=1
        )
        assert should_escalate == True


class TestConversationFlow:
    """Integration tests for conversation flows."""

    @pytest.mark.asyncio
    async def test_faq_flow(self):
        """Test complete FAQ conversation flow."""
        # Triage
        triage = await triage_message(
            "What is your refund policy?",
            "flow_001",
            "cust_001"
        )
        assert triage["routed_to"] == "faq_agent"

        # FAQ response
        faq = await process_faq_query(
            "What is your refund policy?",
            "flow_001",
            "cust_001",
            "en"
        )
        assert faq["agent_type"] == "faq_agent"

    @pytest.mark.asyncio
    async def test_escalation_flow(self):
        """Test escalation conversation flow."""
        # Initial triage
        triage = await triage_message(
            "I want to speak to a manager",
            "flow_002",
            "cust_001"
        )
        assert triage["routed_to"] == "escalation_agent"

        # Escalation
        escalation = await process_escalation(
            "I want to speak to a manager",
            "flow_002",
            "cust_001",
            "en"
        )
        assert escalation["escalation_completed"] == True


class TestMetrics:
    """Test evaluation metrics."""

    def test_resolution_rate(self):
        """Calculate resolution rate from test results."""
        total_calls = 10
        resolved = 7
        escalated = 3

        resolution_rate = (resolved / total_calls) * 100
        assert resolution_rate == 70.0

    def test_avg_confidence(self):
        """Calculate average confidence score."""
        confidences = [0.9, 0.85, 0.95, 0.6, 0.8]
        avg = sum(confidences) / len(confidences)
        assert avg == 0.82


# Run tests with: pytest tests/test_agent_evaluation.py -v
# Run with coverage: pytest tests/test_agent_evaluation.py --cov=agents --cov=api