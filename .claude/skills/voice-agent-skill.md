---
name: voice-agent-skill
description: Voice agent patterns for customer support - tone, escalation, 150-word TTS limit, bilingual (English/Urdu) responses
---

# Voice Agent Skill

Patterns for building voice-first customer support agents with TTS constraints.

## Voice Response Rules

All voice responses must follow these rules:

1. **Plain text only** - No markdown, no bullet points, no special formatting
2. **Max 150 words** - TTS constraint, keep responses concise
3. **No internal jargon** - Customer-facing language only
4. **Always end with clear question or action** - Guide conversation forward
5. **Bilingual support** - Detect input language, respond in same language

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Voice Channel                                 │
│  (Twilio → Deepgram STT → Agent → ElevenLabs TTS → Customer)     │
└─────────────────────────────────────────────────────────────────────┘
```

## Response Templates

### Order Status

**English:**
"Your order #[order_id] is [status]. Tracking number is [tracking]. Expected delivery is [date]. Can I help you with anything else?"

**Urdu:**
"Ap ka order [order_id] [status] hai. Tracking number hai [tracking]. Delivery [date] tak expected hai. Kya main aur kuch madad kar sakta hoon?"

### Appointment Booking

**English:**
"We have availability on [date] at [slots]. Which time works best for you?"

**Urdu:**
"[date] ko available slots hain: [slots]. Ap konsa time prefer karen ge?"

### Escalation

**English:**
"I'm connecting you with [agent_name]. They will contact you [timeframe]. Is there anything else I can help you with?"

**Urdu:**
"Main ap ko [agent_name] se connect kar raha hoon. Woh [timeframe] mein ap se contact karen gi. Kya main aur kuch madad kar sakta hoon?"

### FAQ

**English:**
"[Answer to question]. Can I help you with anything else?"

**Urdu:**
"[Sawalon ka jawab]. Kya main aur kuch madad kar sakta hoon?"

## Tone Guidelines

| Situation | English Tone | Urdu Tone |
|-----------|--------------|----------|
| Greeting | Warm, professional | گرم، پیشہ ورانہ |
| Informing | Clear, concise | واضح، مختصر |
| Problem | Empathetic | ہمدردانہ |
| Closing | Helpful, available | مددگار، دستیاب |

## Escalation Triggers

1. Customer explicitly requests human agent
2. Issue unresolved after 2 conversation turns
3. Low confidence (< 0.6) on intent classification
4. Complex billing disputes or technical issues
5. Complaints about service quality

## Language Detection

```python
URDU_KEYWORDS = ["kya", "kaise", "kab", "kahan", "kyun", "mein", "hum", "ap", "hai", "tha"]
ENGLISH_KEYWORDS = ["what", "how", "when", "where", "why", "i", "me", "you", "is", "are"]

def detect_language(text: str) -> str:
    text_lower = text.lower()
    ur_count = sum(1 for kw in URDU_KEYWORDS if kw in text_lower)
    en_count = sum(1 for kw in ENGLISH_KEYWORDS if kw in text_lower)
    return "ur" if ur_count > en_count else "en"
```

## Testing Voice Responses

```python
def test_voice_response(response: str, max_words: int = 150):
    words = response.split()
    assert len(words) <= max_words, f"Response too long: {len(words)} words"
    assert response == response.strip(), "Response has leading/trailing whitespace"
    assert not any(c in response for c in ["#", "*", "-", "**"]), "Contains markdown"
```

## Bilingual Templates

| English | Urdu |
|---------|------|
| Hello | Salam |
| Thank you | Shukriya |
| How can I help? | Main ap ki kaise madad kar sakta hoon? |
| Please wait | Barah meherbani intezar karen |
| I'm connecting you | Main ap ko connect kar raha hoon |
| Can I help with anything else? | Kya main aur kuch madad kar sakta hoon? |
