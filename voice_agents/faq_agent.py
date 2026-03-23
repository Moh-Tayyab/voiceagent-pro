"""
FAQ Agent - Handles common questions using knowledge-mcp

Built with OpenAI Agents SDK. Searches knowledge base and fetches policies.
"""

import os
import logging
from typing import Optional, Dict, Any

from agents import Agent, Runner

logger = logging.getLogger(__name__)


# FAQ Agent definition using OpenAI Agents SDK
faq_agent = Agent(
    name="FAQ Agent",
    instructions="""You are a customer support FAQ specialist agent. Your job is to:
1. Search the knowledge base for relevant FAQs
2. Fetch policy documents when requested
3. Provide clear, concise answers in plain text
4. Stay under 150 words per response (TTS constraint)
5. Respond in the same language as the customer (English or Urdu)

Do not use markdown, bullet points, or special formatting. Speak naturally as if on a phone call.""",
    model="claude-sonnet-4-20250514"
)


async def search_knowledge_base(
    query: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Search the knowledge base using knowledge-mcp server.

    In production, this calls the knowledge-mcp search_faq tool.
    """
    try:
        logger.info(f"Searching knowledge base: {query}, language={language}")

        # Placeholder: In production, call knowledge-mcp via MCP client
        # from mcp.clients import KnowledgeMCPClient
        # result = await KnowledgeMCPClient.search_faq(query, language)

        # Mock response for now
        return {
            "status": "success",
            "data": {
                "query": query,
                "language": language,
                "results": [
                    {
                        "id": "faq_001",
                        "question": "What is your refund policy?",
                        "answer": "We offer full refunds within 30 days of purchase.",
                        "relevance_score": 0.95
                    }
                ],
                "total_matches": 1
            }
        }

    except Exception as e:
        logger.error(f"Knowledge base search error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "SEARCH_ERROR",
                "message": str(e)
            }
        }


async def fetch_policy(policy_name: str) -> Dict[str, Any]:
    """
    Fetch a policy document using knowledge-mcp server.

    In production, this calls the knowledge-mcp get_policy tool.
    """
    try:
        logger.info(f"Fetching policy: {policy_name}")

        # Placeholder: In production, call knowledge-mcp via MCP client
        # from mcp.clients import KnowledgeMCPClient
        # result = await KnowledgeMCPClient.get_policy(policy_name)

        # Mock response for now
        return {
            "status": "success",
            "data": {
                "policy_name": policy_name,
                "title": "Refund and Return Policy",
                "content": "Customers may request a full refund within 30 days of purchase.",
                "version": "1.2"
            }
        }

    except Exception as e:
        logger.error(f"Policy fetch error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "POLICY_ERROR",
                "message": str(e)
            }
        }


async def process_faq_query(
    message: str,
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Process an FAQ query through the FAQ agent.

    Args:
        message: Customer question
        session_id: Unique session identifier
        customer_id: Optional customer ID
        language: Language preference

    Returns:
        Dict with FAQ response and source info
    """
    try:
        logger.info(f"FAQ processing session={session_id}")

        # Search knowledge base
        search_result = await search_knowledge_base(message, language)

        if search_result.get("status") == "success" and search_result.get("data", {}).get("results"):
            top_result = search_result["data"]["results"][0]

            # Format response for voice (plain text, under 150 words)
            response_text = format_voice_response(
                top_result["answer"],
                language
            )

            return {
                "session_id": session_id,
                "customer_id": customer_id,
                "response_text": response_text,
                "agent_type": "faq_agent",
                "confidence": top_result.get("relevance_score", 0.8),
                "source": {
                    "type": "faq",
                    "id": top_result.get("id"),
                    "question": top_result.get("question")
                },
                "language": language,
                "handoff_to": None
            }
        else:
            # No FAQ match found - escalate
            return {
                "session_id": session_id,
                "customer_id": customer_id,
                "response_text": get_fallback_response(language),
                "agent_type": "faq_agent",
                "confidence": 0.4,
                "source": None,
                "language": language,
                "handoff_to": "escalation_agent"
            }

    except Exception as e:
        logger.error(f"FAQ processing error: {str(e)}")
        return {
            "session_id": session_id,
            "error": str(e),
            "response_text": "I apologize, but I'm having trouble accessing our knowledge base. Let me connect you with a specialist.",
            "agent_type": "faq_agent",
            "confidence": 0.0,
            "handoff_to": "escalation_agent"
        }


def format_voice_response(answer: str, language: str) -> str:
    """
    Format answer for voice output.

    Rules:
    - Plain text only (no markdown)
    - Max 150 words
    - Natural conversational tone
    - End with question or action if appropriate
    """
    # Remove any markdown formatting
    answer = answer.replace("#", "").replace("*", "").replace("-", "")

    # Truncate if too long (150 words max)
    words = answer.split()
    if len(words) > 150:
        answer = " ".join(words[:150])

    # Ensure natural ending
    if language == "ur":
        if not answer.endswith("?") and not answer.endswith("."):
            answer = answer + " Kya main aur kuch madad kar sakta hoon?"
    else:
        if not answer.endswith("?") and not answer.endswith("."):
            answer = answer + " Can I help you with anything else?"

    return answer


def get_fallback_response(language: str) -> str:
    """
    Get fallback response when FAQ search yields no results.
    """
    if language == "ur":
        return "Maaf kijiye, mujhe ap ke sawal ka jawab nahi mila. Kya main ap ko kisi specialist se connect kar don?"
    return "I apologize, but I couldn't find an answer to your question in our FAQs. Would you like me to connect you with a specialist who can help?"


async def run_faq_agent(
    message: str,
    context: Optional[list] = None
) -> str:
    """
    Run the FAQ agent using OpenAI Agents SDK.

    This executes the full agent with knowledge-mcp tool access.
    """
    try:
        # Build conversation history
        conversation_history = context or []
        conversation_history.append({"role": "user", "content": message})

        # Run the agent
        result = await Runner.run(
            faq_agent,
            conversation_history
        )

        return result.final_output

    except Exception as e:
        logger.error(f"FAQ agent run error: {str(e)}")
        return get_fallback_response("en")