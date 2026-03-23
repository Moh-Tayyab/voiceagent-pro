---
name: agent-testing-skill
description: Evaluation script structure for testing voice agents with bilingual (English/Urdu) test cases
---

# Agent Testing Skill

Evaluation scripts for testing voice agent responses.

## Test Structure

```
tests/
├── test_agents.py          # Unit tests for agent functions
├── test_integration.py     # Integration tests with MCP servers
├── conftest.py            # Pytest fixtures
├── fixtures/
│   ├── urdu_queries.json   # Urdu test queries
│   ├── english_queries.json # English test queries
│   └── expected_responses.json # Expected response patterns
└── evaluation/
    ├── run_evaluation.py  # Main evaluation script
    └── report.py          # Results reporting
```

## Test Fixtures Format

```json
{
  "urdu_queries": [
    {
      "id": "ur_001",
      "query": "Main apna order cancel karna chahta hun",
      "expected_intent": "billing",
      "expected_language": "ur",
      "escalation_allowed": true
    },
    {
      "id": "ur_002",
      "query": "Mera invoice galat hai",
      "expected_intent": "billing",
      "expected_language": "ur",
      "escalation_allowed": false
    }
  ],
  "english_queries": [
    {
      "id": "en_001",
      "query": "I need to reschedule my appointment",
      "expected_intent": "booking",
      "expected_language": "en",
      "escalation_allowed": false
    },
    {
      "id": "en_002",
      "query": "I want to speak to a human agent",
      "expected_intent": "escalation",
      "expected_language": "en",
      "escalation_allowed": true
    }
  ]
}
```

## Unit Test Example

```python
# tests/test_agents.py
import pytest
from agents.triage_agent import detect_language, detect_intent, triage_message

class TestLanguageDetection:
    def test_detect_urdu(self):
        assert detect_language("Main apna order cancel karna chahta hun") == "ur"

    def test_detect_english(self):
        assert detect_language("I need to reschedule my appointment") == "en"

    def test_detect_mixed(self):
        # Should default to English for mixed
        result = detect_language("Hello, main order cancel karna chahta hun")
        assert result in ["en", "ur"]

class TestIntentClassification:
    def test_billing_intent_urdu(self):
        intent, confidence = detect_intent("Mera invoice galat hai")
        assert intent == Intent.BILLING

    def test_booking_intent_english(self):
        intent, confidence = detect_intent("I need to reschedule my appointment")
        assert intent == Intent.BOOKING

    def test_escalation_intent(self):
        intent, confidence = detect_intent("I want to speak to a human")
        assert intent == Intent.ESCALATION

@pytest.mark.asyncio
class TestTriageAgent:
    async def test_triage_returns_structured_response(self):
        result = await triage_message(
            message="I need to reschedule my appointment",
            session_id="test_123"
        )
        assert "session_id" in result
        assert "intent" in result
        assert "language" in result
        assert "routed_to" in result
        assert result["confidence"] >= 0.0
```

## Integration Test Example

```python
# tests/test_integration.py
import pytest
from agents.triage_agent import triage_message
from agents.billing_agent import process_billing_query
from agents.booking_agent import process_booking_request

@pytest.mark.asyncio
async def test_full_triage_to_billing_pipeline():
    """Test complete flow from triage to billing agent."""
    # Step 1: Triage the message
    triage_result = await triage_message(
        message="I need to check my order status",
        session_id="test_full_001"
    )

    assert triage_result["intent"] == "billing"
    assert triage_result["routed_to"] == "billing_agent"

    # Step 2: Process with billing agent
    billing_result = await process_billing_query(
        message="What's the status of order #12345?",
        session_id="test_full_001",
        customer_id="cust_001"
    )

    assert billing_result["agent_type"] == "billing_agent"
    assert "response_text" in billing_result
```

## Voice Response Validation

```python
# tests/test_voice_response.py
import pytest

def validate_voice_response(response: str, max_words: int = 150):
    """Validate response follows voice response rules."""
    # Check length
    words = response.split()
    assert len(words) <= max_words, f"Response too long: {len(words)} words (max {max_words})"

    # Check no markdown
    markdown_chars = ["#", "*", "-", "**", "__"]
    for char in markdown_chars:
        assert char not in response, f"Response contains markdown character: {char}"

    # Check ends with question or action
    ends_with_action = response.strip().endswith(("?", ".", "!"))
    assert ends_with_action, "Response should end with question or statement"

    # Check no excessive whitespace
    assert response == " ".join(response.split()), "Response has extra whitespace"

class TestVoiceResponseFormat:
    def test_order_status_response_format(self):
        response = "Your order #12345 is shipped. Tracking number is TRK123. Can I help you with anything else?"
        validate_voice_response(response)

    def test_urdu_response_format(self):
        response = "Ap ka order 12345 shipped hai. Tracking number hai TRK123. Kya main aur kuch madad kar sakta hoon?"
        validate_voice_response(response)

    def test_response_too_long(self):
        long_response = " ".join(["word"] * 200)
        with pytest.raises(AssertionError):
            validate_voice_response(long_response)
```

## Evaluation Script

```python
# tests/evaluation/run_evaluation.py
import asyncio
import json
from pathlib import Path
from agents.triage_agent import triage_message, detect_language, detect_intent

async def run_evaluation():
    fixtures_path = Path("tests/fixtures")

    with open(fixtures_path / "urdu_queries.json") as f:
        urdu_queries = json.load(f)["urdu_queries"]

    with open(fixtures_path / "english_queries.json") as f:
        english_queries = json.load(f)["english_queries"]

    results = []

    for query_data in urdu_queries + english_queries:
        query_id = query_data["id"]
        query = query_data["query"]
        expected_intent = query_data["expected_intent"]
        expected_language = query_data["expected_language"]

        detected_language = detect_language(query)
        detected_intent, confidence = detect_intent(query)

        triage_result = await triage_message(query, session_id=query_id)

        results.append({
            "query_id": query_id,
            "query": query,
            "expected_language": expected_language,
            "detected_language": detected_language,
            "language_match": detected_language == expected_language,
            "expected_intent": expected_intent,
            "detected_intent": detected_intent.value,
            "intent_match": detected_intent.value == expected_intent,
            "confidence": confidence,
            "triage_routed_to": triage_result["routed_to"]
        })

    # Calculate metrics
    language_accuracy = sum(1 for r in results if r["language_match"]) / len(results)
    intent_accuracy = sum(1 for r in results if r["intent_match"]) / len(results)

    print(f"Language Detection Accuracy: {language_accuracy:.2%}")
    print(f"Intent Classification Accuracy: {intent_accuracy:.2%}")

    return results

if __name__ == "__main__":
    results = asyncio.run(run_evaluation())
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agents --cov-report=html

# Run evaluation
python -m tests.evaluation.run_evaluation

# Run specific test file
pytest tests/test_agents.py -v

# Run with Urdu/English filter
pytest tests/ -k "urdu or english" -v
```
