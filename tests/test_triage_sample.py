"""
Test script for testing core triage logic without requiring openai-agents SDK.
Tests language detection, intent classification, and response formatting.
"""
import sys
sys.path.insert(0, '/home/muhammad_tayyab/hackathon/VoiceAgent_Pro')

# Import from voice_agents (renamed from agents)
from voice_agents.triage_agent import (
    detect_language,
    detect_intent,
    get_triage_response
)
from enum import Enum


class Intent(str, Enum):
    FAQ = "faq"
    BILLING = "billing"
    BOOKING = "booking"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"
    GENERAL = "general"


SAMPLE_QUERIES = [
    {
        "id": "ur_001",
        "query": "Main apna order cancel karna chahta hun",  # Urdu: I want to cancel my order
        "expected_intent": "billing",
        "expected_language": "ur",
        "description": "Urdu - Order cancellation"
    },
    {
        "id": "en_001",
        "query": "I need to reschedule my appointment",  # English - Appointment reschedule
        "expected_intent": "booking",
        "expected_language": "en",
        "description": "English - Appointment reschedule"
    },
    {
        "id": "ur_002",
        "query": "Mera invoice galat hai",  # Urdu - My invoice is wrong
        "expected_intent": "billing",
        "expected_language": "ur",
        "description": "Urdu billing query"
    }
]


def validate_voice_response(response: str, max_words: int = 150) -> tuple[bool, str]:
    """Validate response follows voice response rules."""
    if not response:
        return False, "Empty response"

    # Check length
    words = response.split()
    if len(words) > max_words:
        return False, f"Too long: {len(words)} words (max {max_words})"

    # Check no markdown
    markdown_chars = ["#", "*", "-"]
    for char in markdown_chars:
        if char in response:
            return False, f"Contains markdown: {char}"

    # Check ends with question or action
    if not response.strip().endswith(("?", ".", "!")):
        return False, "Doesn't end with question or statement"

    return True, "OK"


def run_tests():
    print("=" * 70)
    print("VoiceAgent Pro - Triage Agent Test Results")
    print("=" * 70)

    results = []

    for query_data in SAMPLE_QUERIES:
        query_id = query_data["id"]
        query = query_data["query"]
        expected_intent = query_data["expected_intent"]
        expected_language = query_data["expected_language"]
        description = query_data["description"]

        print(f"\n[{query_id}] {description}")
        print(f"Query: \"{query}\"")

        # Detect language
        detected_language = detect_language(query)
        language_match = detected_language == expected_language
        print(f"Language: expected={expected_language}, detected={detected_language} {'✓' if language_match else '✗'}")

        # Detect intent
        detected_intent, confidence = detect_intent(query)
        intent_match = detected_intent.value == expected_intent
        print(f"Intent: expected={expected_intent}, detected={detected_intent.value} (conf={confidence:.2f}) {'✓' if intent_match else '✗'}")

        # Get voice response
        response_text = get_triage_response(detected_intent, detected_language)
        print(f"Response: {response_text[:80]}...")

        # Validate response format
        voice_valid, voice_msg = validate_voice_response(response_text)
        print(f"Voice format: {voice_msg}")

        results.append({
            "query_id": query_id,
            "language_match": language_match,
            "intent_match": intent_match,
            "voice_valid": voice_valid
        })

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    language_acc = sum(1 for r in results if r["language_match"]) / len(results) * 100
    intent_acc = sum(1 for r in results if r["intent_match"]) / len(results) * 100
    voice_acc = sum(1 for r in results if r["voice_valid"]) / len(results) * 100

    print(f"Language Detection Accuracy: {language_acc:.0f}%")
    print(f"Intent Classification Accuracy: {intent_acc:.0f}%")
    print(f"Voice Response Format: {voice_acc:.0f}%")

    all_passed = True
    for r in results:
        status = "PASS" if r["language_match"] and r["intent_match"] and r["voice_valid"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  [{status}] {r['query_id']}")

    print("\n" + "=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
