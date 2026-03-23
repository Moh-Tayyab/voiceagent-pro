**Voice Agent Platform**

Customer Support Automation

*Product Requirements Document v1.0*

  -----------------------------------------------------------------------
  *Purpose: Provide Claude (and any developer) complete context to build,
  scaffold, and iterate on this project using spec-driven development.*

  -----------------------------------------------------------------------

Stack: Python \| FastAPI \| FastMCP \| OpenAI Agents SDK \| Claude Code

**1. Executive Summary**

This project builds a production-ready Voice Agent Platform for customer
support automation. The platform is designed to be sold as a SaaS
product to businesses needing AI-powered phone/chat support. Claude
serves as the core intelligence layer via MCP (Model Context Protocol)
servers, while OpenAI Agents SDK handles orchestration and routing.

  -----------------------------------------------------------------------
  *Key Insight: MCP servers are the sellable, reusable asset. Each client
  gets a customized set of MCP servers (knowledge, CRM, ticketing)
  deployed independently, while the core agent infrastructure remains
  shared.*

  -----------------------------------------------------------------------

  --------------------- -------------------------------------------------
  **Field**             Detail

  **Product Name**      VoiceAgent Pro

  **Primary Market**    SMBs & Enterprises (any industry with phone
                        support)

  **Revenue Model**     Monthly SaaS subscription (3 tiers)

  **Primary Language**  English + Urdu (bilingual by default)

  **Deployment Target** Railway / Render / AWS (per client)

  **Core Philosophy**   Claude = brain via MCP, Agents SDK = hands &
                        routing
  --------------------- -------------------------------------------------

**2. Problem Statement**

Businesses spend heavily on human customer support agents who handle
repetitive queries (order status, FAQs, appointment booking, refund
policies). These agents are expensive, not available 24/7, and
inconsistent in quality. Current AI chatbot solutions lack:

-   Natural voice interaction (phone-native experience)

-   Deep integration with company-specific knowledge bases

-   Intelligent escalation and handoff logic

-   Multi-language support for regional markets (Urdu, Arabic, etc.)

**3. Solution Architecture**

**3.1 High-Level Flow**

Customer speaks → STT converts to text → FastAPI receives → Agents SDK
orchestrates → Claude reasons via MCP tools → Response text generated →
TTS converts to audio → Customer hears answer.

  -----------------------------------------------------------------------
  *Design Principle: Every external call (CRM, database, ticketing) MUST
  go through an MCP server. No direct API calls from agent logic. This
  keeps the system modular, testable, and swappable per client.*

  -----------------------------------------------------------------------

**3.2 Technology Stack**

  --------------------- -------------------------------------------------
  **Layer**             Technology / Service

  **Voice Input (STT)** Deepgram (primary) / OpenAI Whisper (fallback)

  **Voice Output        ElevenLabs (primary) / Azure TTS (fallback)
  (TTS)**               

  **Telephony**         Twilio (inbound calls) / WebSocket for web widget

  **API Gateway**       FastAPI (Python 3.11+) with async handlers

  **Agent               OpenAI Agents SDK (handoffs, guardrails, tool
  Orchestration**       use)

  **Intelligence        Claude via Anthropic API (called through MCP
  Layer**               tools)

  **MCP Servers**       FastMCP (Python) --- deployed as separate
                        microservices

  **Database**          PostgreSQL (sessions, logs) + Redis (caching,
                        rate limits)

  **Deployment**        Docker + Railway/Render (per microservice)

  **Dev Environment**   Claude Code with MCP clients + CLAUDE.md context
  --------------------- -------------------------------------------------

**4. MCP Server Specifications**

Each MCP server is a FastMCP Python application deployed as a standalone
microservice. Claude Code connects to these via SSE transport during
development. Production agents call them through the Agents SDK tool
wrappers.

**4.1 MCP Server Inventory**

  ---------------- ---------------- -------------------------------------
  **Server Name**  **Port (dev)**   **Responsibility**

  knowledge-mcp    8001             FAQs, product docs, policy lookups
                                    --- customized per client

  crm-mcp          8002             Customer lookup, history, account
                                    info (HubSpot/Salesforce/custom)

  ticketing-mcp    8003             Create, update, escalate support
                                    tickets (Zendesk/Freshdesk/custom)

  calendar-mcp     8004             Appointment booking, availability
                                    checks, rescheduling

  analytics-mcp    8005             Log call outcomes, generate reports,
                                    track resolution rates

  escalation-mcp   8006             Route to human agent, send SMS/email
                                    alerts, PagerDuty integration
  ---------------- ---------------- -------------------------------------

**4.2 MCP Server Template Structure**

> \# servers/knowledge_mcp.py
>
> from fastmcp import FastMCP
>
> mcp = FastMCP(\'knowledge-server\')
>
> \@mcp.tool()
>
> async def search_faq(query: str, language: str = \'en\') -\> str:
>
> \'\'\'Search company FAQs. Returns top 3 relevant answers.\'\'\'
>
> \...
>
> \@mcp.tool()
>
> async def get_policy(policy_name: str) -\> str:
>
> \'\'\'Fetch a specific policy document by name.\'\'\'
>
> \...
>
> if \_\_name\_\_ == \'\_\_main\_\_\':
>
> mcp.run(transport=\'sse\', port=8001)

**4.3 Claude Code MCP Configuration**

File: .claude/settings.json (project root)

> {
>
> \"mcpServers\": {
>
> \"knowledge\": { \"url\": \"http://localhost:8001/sse\",
> \"permissions\": \[\"read\"\] },
>
> \"crm\": { \"url\": \"http://localhost:8002/sse\", \"permissions\":
> \[\"read\"\] },
>
> \"ticketing\": { \"url\": \"http://localhost:8003/sse\",
> \"permissions\": \[\"write\"\] },
>
> \"calendar\": { \"url\": \"http://localhost:8004/sse\",
> \"permissions\": \[\"read\", \"write\"\] }
>
> }
>
> }

**5. Claude Code Setup**

**5.1 CLAUDE.md --- Project Root**

This file is the single source of truth for Claude Code. Every session
starts here.

> \# VoiceAgent Pro --- Claude Context
>
> \## Project Goal
>
> Build a voice agent platform for customer support.
>
> Sell as SaaS. Claude is the brain via MCP tools.
>
> \## Stack Rules
>
> \- Python 3.11+ only
>
> \- FastAPI for all HTTP endpoints
>
> \- FastMCP for all MCP servers
>
> \- OpenAI Agents SDK for orchestration
>
> \- All external calls go through MCP --- never direct
>
> \- Async everywhere (asyncio)
>
> \## Voice Response Rules
>
> \- Max 150 words per response (TTS constraint)
>
> \- No markdown, no bullet points in voice responses
>
> \- Always end with a clear question or action
>
> \- Bilingual: detect language, respond in same language

**5.2 Skills to Create**

Place in .claude/skills/ directory:

  ----------------------------- -------------------------------------------------
  **Skill File**                Purpose

  **voice-agent-skill.md**      Agent persona, escalation rules, tone guidelines,
                                max response length

  **fastmcp-server-skill.md**   Template for creating new MCP servers with error
                                handling

  **fastapi-route-skill.md**    Route structure, auth middleware, WebSocket
                                handler patterns

  **agent-testing-skill.md**    How to write evaluation scripts for agent
                                conversations

  **deployment-skill.md**       Docker, Railway deployment steps per microservice
  ----------------------------- -------------------------------------------------

**5.3 Rules**

Place in .claude/rules/ directory:

-   never-hardcode-secrets.md --- All secrets via environment variables
    only

-   mcp-first.md --- All external calls must use MCP tools, never direct
    HTTP

-   voice-response-format.md --- Response must be plain text, max 150
    words

-   async-required.md --- All FastAPI routes and MCP tools must be async

-   error-handling.md --- All tools return structured error objects,
    never raise raw exceptions

**5.4 Permissions Model**

Permissions are scoped per MCP server and per agent type:

  --------------------- -------------------------------------------------
  **Agent Type**        Allowed MCP Permissions

  **Tier 1 --- FAQ      knowledge:read only
  Bot**                 

  **Tier 2 --- Support  knowledge:read, crm:read, ticketing:write
  Agent**               

  **Tier 3 --- Full     All servers with read+write
  Agent**               

  **Claude Code (dev)** All servers read-only except ticketing and
                        escalation
  --------------------- -------------------------------------------------

**6. Agent Architecture**

**6.1 Agent Hierarchy**

Built with OpenAI Agents SDK. Each agent has a specific role and can
hand off to others:

-   **Triage Agent --- Entry point. Detects intent, routes to specialist
    agent**

    -   Detects language (Urdu/English)

    -   Classifies: FAQ / billing / booking / complaint / escalation

-   **FAQ Agent --- Handles common questions using knowledge-mcp**

    -   Searches knowledge base, fetches policies

-   **Billing Agent --- Order status, refunds, payment queries using
    crm-mcp**

-   **Booking Agent --- Appointments via calendar-mcp**

-   **Escalation Agent --- Routes to human, creates urgent ticket via
    escalation-mcp**

**6.2 Guardrails**

-   Input guardrail: Filter profanity, PII detection before processing

-   Output guardrail: Ensure response is under 150 words, no sensitive
    data leaked

-   Escalation trigger: If confidence \< 0.6 or issue unresolved after 2
    turns, escalate

-   Timeout: Agent must respond within 3 seconds or acknowledge and
    continue

**6.3 Claude Integration Pattern**

Claude is invoked for complex reasoning tasks (multi-step problem
solving, ambiguous queries). The pattern:

> \# Inside an Agents SDK tool
>
> async def analyze_complex_issue(context: str) -\> str:
>
> response = await anthropic_client.messages.create(
>
> model=\'claude-sonnet-4-20250514\',
>
> max_tokens=500,
>
> system=\'You are a customer support expert. Be concise.\',
>
> messages=\[{\'role\': \'user\', \'content\': context}\]
>
> )
>
> return response.content\[0\].text

  -----------------------------------------------------------------------
  *This tool is registered in the Agents SDK as any other tool. The agent
  decides when Claude reasoning is needed vs a simple MCP lookup.*

  -----------------------------------------------------------------------

**7. Voice Pipeline Specification**

**7.1 Inbound Call Flow**

  --------------------- -------------------------------------------------
  **Step**              Implementation

  **1. Call arrives**   Twilio webhook → FastAPI /inbound endpoint

  **2. Speech           Twilio Media Streams (WebSocket) → audio chunks
  captured**            

  **3. STT**            Deepgram real-time transcription → text

  **4. Agent            OpenAI Agents SDK with MCP tools
  processes**           

  **5. TTS**            ElevenLabs text-to-speech → audio bytes

  **6. Audio played**   Stream back via Twilio TTS or WebSocket

  **7. Session logged** analytics-mcp logs outcome, duration, resolution
  --------------------- -------------------------------------------------

**7.2 Latency Targets**

-   STT processing: \< 500ms

-   Agent + MCP tools: \< 2000ms total

-   TTS generation: \< 800ms

-   End-to-end response time: \< 3.5 seconds

**8. Business Model & Pricing**

**8.1 Subscription Tiers**

  ------------------ --------------- ------------------ ------------------
  **Tier**           **Price         **Agents**         **MCP Servers
                     (USD/mo)**                         Included**

  **Starter**        \$299           1 agent            knowledge-mcp (500
                                                        FAQs)

  **Professional**   \$799           3 agents +         knowledge + crm +
                                     handoffs           ticketing

  **Enterprise**     \$2,000+        Unlimited +        All 6 MCP
                                     white-label        servers + custom
  ------------------ --------------- ------------------ ------------------

**8.2 One-Time Setup Fees**

-   Starter setup: \$500 (onboarding, FAQ upload, testing)

-   Professional setup: \$1,500 (CRM integration, custom persona, UAT)

-   Enterprise setup: \$5,000+ (custom MCP development, multi-language,
    SLA)

**8.3 Client Deliverables**

-   Deployed MCP servers (per client subdomain/Railway project)

-   Customized CLAUDE.md + skills for their domain

-   Agent persona configuration (name, tone, escalation rules)

-   Dashboard access (call logs, resolution rate, analytics)

-   Monthly usage report via analytics-mcp

**9. Project Folder Structure**

> voiceagent-pro/
>
> ├── CLAUDE.md \# Claude Code context
>
> ├── .claude/
>
> │ ├── settings.json \# MCP server connections + permissions
>
> │ ├── skills/ \# Reusable skill files
>
> │ └── rules/ \# Behavior rules
>
> ├── api/ \# FastAPI app
>
> │ ├── main.py
>
> │ ├── routes/
>
> │ └── middleware/
>
> ├── agents/ \# OpenAI Agents SDK agents
>
> │ ├── triage_agent.py
>
> │ ├── faq_agent.py
>
> │ ├── billing_agent.py
>
> │ └── escalation_agent.py
>
> ├── servers/ \# FastMCP microservices
>
> │ ├── knowledge_mcp.py
>
> │ ├── crm_mcp.py
>
> │ ├── ticketing_mcp.py
>
> │ ├── calendar_mcp.py
>
> │ └── analytics_mcp.py
>
> ├── voice/ \# STT + TTS handlers
>
> │ ├── deepgram_stt.py
>
> │ └── elevenlabs_tts.py
>
> ├── tests/ \# Agent evaluation scripts
>
> ├── docker-compose.yml
>
> └── requirements.txt

**10. Development Phases**

**Phase 1 --- Foundation (Week 1-2)**

-   **Set up FastAPI project structure + CLAUDE.md**

-   **Build knowledge-mcp server (FAQ search)**

-   **Build crm-mcp server (customer lookup)**

-   **Create Claude Code skills + rules files**

-   **Basic Triage + FAQ agent with OpenAI Agents SDK**

**Phase 2 --- Voice Pipeline (Week 3-4)**

-   **Deepgram STT integration via WebSocket**

-   **ElevenLabs TTS integration**

-   **Twilio inbound call webhook**

-   **End-to-end call test (speech in → speech out)**

**Phase 3 --- Full Agent Suite (Week 5-6)**

-   **ticketing-mcp + calendar-mcp + escalation-mcp**

-   **All specialist agents with handoff logic**

-   **Guardrails (input/output validation)**

-   **Analytics dashboard (basic)**

**Phase 4 --- Productization (Week 7-8)**

-   **Multi-tenant isolation (per-client MCP server instances)**

-   **Billing/subscription system**

-   **Client onboarding automation**

-   **Load testing + latency optimization**

**11. Constraints & Non-Negotiables**

  -----------------------------------------------------------------------
  *These rules are absolute. Claude Code must enforce them in every file
  it generates.*

  -----------------------------------------------------------------------

-   All external API calls go through MCP servers --- NEVER direct from
    agent logic

-   All secrets in environment variables --- NEVER hardcoded

-   All FastAPI routes and MCP tools must be async (asyncio)

-   Voice responses: plain text only, max 150 words, no markdown

-   Every MCP tool must return a structured response (dict) --- never
    raise raw exceptions

-   Per-client data isolation --- one PostgreSQL schema or database per
    client

-   Claude is called for reasoning only --- simple lookups go directly
    to MCP tools

**12. Success Metrics**

  --------------------- -------------------------------------------------
  **Metric**            Target

  **First response      \< 3.5 seconds end-to-end
  latency**             

  **FAQ resolution      \> 75% without human escalation
  rate**                

  **STT accuracy**      \> 92% word error rate

  **Agent uptime**      99.5% monthly

  **Client onboarding   \< 3 business days for Starter tier
  time**                

  **Monthly churn       \< 5%
  target**              
  --------------------- -------------------------------------------------

  -----------------------------------------------------------------------
  *This document is intended as a living spec. Update it as the product
  evolves. When giving this to Claude Code, place it in the project root
  as requirements.md and reference it in CLAUDE.md.*

  -----------------------------------------------------------------------
