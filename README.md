# voiceagent-pro — Realtime Voice AI Agent for Customer Support

> **Business value:** Customer calls ka wait khatam. Ye agent phone/voice par baat karta hai, samajhta hai, aur action leta hai — FAQ jawab, booking, ticket, human ko handoff.

**Stack:** Python 3.11, FastAPI, OpenAI Agents SDK, FastMCP, Twilio, Deepgram, ElevenLabs, PostgreSQL, Redis, Docker Compose

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-009688) ![Docker](https://img.shields.io/badge/Docker-ready-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## Demo
🎥 Loom video: (LINK DALO — 2 min: call → transcript → AI reply → tool call)
🟢 Live API docs: `http://your-server:8000/docs` (deploy ke baad)

## What it does
- Voice in/out: Twilio → Deepgram STT → Claude brain → ElevenLabs TTS
- 4 specialist agents: `faq_agent`, `booking_agent`, `billing_agent`, `escalation_agent` + `triage_agent` router
- 6 MCP tools (never direct calls): Knowledge, CRM, Ticketing, Calendar, Analytics, Escalation
- Voice rules: max 150 words/reply, no markdown in voice, bilingual detect-and-reply
- Human handoff via PagerDuty + ticket in Zendesk

## Run in 3 commands
```bash
cp .env.example .env   # keys bharo: ANTHROPIC, OPENAI, TWILIO, DEEPGRAM, ELEVENLABS
docker compose up --build
curl localhost:8000/health
```

Local (without Docker):
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
pytest tests/ -v
```

## Structure
```
api/            # FastAPI app (routes, middleware, services)
voice_agents/   # triage, faq, booking, billing, escalation
servers/        # 6 MCP servers (knowledge, crm, ticketing, calendar, analytics, escalation)
voice/          # deepgram_stt.py, elevenlabs_tts.py
tests/          # agent evaluation + triage tests
Dockerfile.api  # API service
Dockerfile.mcp  # MCP services
docker-compose.yml  # api + 6 mcp + postgres + redis = 9 services
```

## MCP ports (dev)
API 8000 | Knowledge 8001 | CRM 8002 | Ticketing 8003 | Calendar 8004 | Analytics 8005 | Escalation 8006

## What I can build for you
Same engine se aapke liye: clinic booking voice bot, shop support bot, WhatsApp voice bot. Email: m.tayyab1263@gmail.com — free 15-min call par bataunga AI aapka time bacha sakta hai ya nahi.
