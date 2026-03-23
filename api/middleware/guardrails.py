"""
Guardrails Middleware - Input/output validation, PII detection, profanity filter

Ensures safe and appropriate agent responses.
"""

import os
import re
import logging
from typing import Optional, Set, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


# Profanity word list (curated for customer support context)
PROFANITY_WORDS: Set[str] = {
    "damn", "hell", "crap", "bastard"
    # Add more as needed for production
}

# PII patterns
PII_PATTERNS: Dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "phone": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
}

# Input length limits
MAX_INPUT_LENGTH = 500  # characters
MIN_INPUT_LENGTH = 5    # characters


class Guardrails:
    """
    Input and output guardrails for voice agent.

    Validates:
    - Input length
    - Profanity detection
    - PII detection
    - Output word count
    - Sensitive data leakage
    """

    def __init__(self):
        """Initialize guardrails."""
        self.profanity_words = PROFANITY_WORDS
        self.pii_patterns = PII_PATTERNS

    def validate_input(self, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate input text.

        Args:
            text: Input text to validate

        Returns:
            Tuple of (is_valid, validation_result)
        """
        result = {
            "valid": True,
            "length_ok": True,
            "profanity_detected": False,
            "pii_detected": False,
            "pii_types": [],
            "warnings": []
        }

        # Check length
        if len(text) > MAX_INPUT_LENGTH:
            result["valid"] = False
            result["length_ok"] = False
            result["warnings"].append(f"Input exceeds {MAX_INPUT_LENGTH} characters")

        if len(text) < MIN_INPUT_LENGTH:
            result["valid"] = False
            result["warnings"].append(f"Input too short (min {MIN_INPUT_LENGTH} chars)")

        # Check profanity
        text_lower = text.lower()
        for word in self.profanity_words:
            if word in text_lower:
                result["profanity_detected"] = True
                result["warnings"].append("Profanity detected")
                break

        # Check PII
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                result["pii_detected"] = True
                result["pii_types"].append(pii_type)
                result["warnings"].append(f"PII detected: {pii_type}")

        return result["valid"], result

    def validate_output(
        self,
        text: str,
        max_words: int = 150
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate output text for voice response.

        Args:
            text: Output text to validate
            max_words: Maximum word count (default 150 for TTS)

        Returns:
            Tuple of (is_valid, validation_result)
        """
        result = {
            "valid": True,
            "word_count_ok": True,
            "word_count": 0,
            "has_markdown": False,
            "pii_detected": False,
            "warnings": []
        }

        # Count words
        words = text.split()
        result["word_count"] = len(words)

        if len(words) > max_words:
            result["valid"] = False
            result["word_count_ok"] = False
            result["warnings"].append(f"Response exceeds {max_words} words")

        # Check for markdown (not allowed in voice responses)
        if any(char in text for char in ["#", "*", "_", "`", "[", "]"]):
            result["has_markdown"] = True
            result["warnings"].append("Markdown formatting detected")

        # Check PII in output (should not leak sensitive data)
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                result["pii_detected"] = True
                result["warnings"].append(f"PII in output: {pii_type}")
                result["valid"] = False

        return result["valid"], result

    def sanitize_input(self, text: str) -> str:
        """
        Sanitize input text by masking PII.

        Args:
            text: Input text

        Returns:
            Sanitized text with PII masked
        """
        sanitized = text

        # Mask credit card numbers
        sanitized = re.sub(
            r"\b(\d{4})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            r"\1-XXXX-XXXX-XXXX",
            sanitized
        )

        # Mask SSN
        sanitized = re.sub(
            r"\b\d{3}-\d{2}-(\d{4})\b",
            r"XXX-XX-\1",
            sanitized
        )

        # Mask email
        sanitized = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL_MASKED]",
            sanitized
        )

        return sanitized

    def check_escalation_trigger(
        self,
        text: str,
        confidence: float,
        turn_count: int
    ) -> bool:
        """
        Check if escalation should be triggered.

        Triggers:
        - Confidence < 0.6
        - Issue unresolved after 2 turns
        - Explicit request for human
        - Complaint indicators

        Args:
            text: Customer message
            confidence: Agent confidence score
            turn_count: Number of conversation turns

        Returns:
            True if escalation should trigger
        """
        # Low confidence
        if confidence < 0.6:
            return True

        # Unresolved after 2 turns
        if turn_count >= 2:
            return True

        # Explicit human request
        human_keywords = ["human", "agent", "supervisor", "manager", "person"]
        if any(keyword in text.lower() for keyword in human_keywords):
            return True

        # Complaint indicators
        complaint_keywords = ["complaint", "unacceptable", "terrible", "awful", "refund"]
        if any(keyword in text.lower() for keyword in complaint_keywords):
            return True

        return False


# Singleton instance
_guardrails: Optional[Guardrails] = None


def get_guardrails() -> Guardrails:
    """Get or create guardrails singleton."""
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails