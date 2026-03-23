# VoiceAgent Pro - Claude Context

## Project Goal

Build a voice agent platform for customer support.

Sell as SaaS. Claude is the brain via MCP tools.

## Stack Rules

- Python 3.11+ only
- FastAPI for all HTTP endpoints
- FastMCP for all MCP servers
- OpenAI Agents SDK for orchestration
- All external calls go through MCP - never direct
- Async everywhere (asyncio)

## Voice Response Rules

- Max 150 words per response (TTS constraint)
- No markdown, no bullet points in voice responses
- Always end with a clear question or action
- Bilingual: detect language, respond in same language