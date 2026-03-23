"""
Knowledge MCP Server - FAQs, product docs, policy lookups

This server provides tools for searching company knowledge bases,
FAQs, and retrieving policy documents.
"""

import os
import logging
from typing import Optional

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("knowledge-server")

# In-memory knowledge base (would be database in production)
KNOWLEDGE_BASE = {
    "faq": [
        {
            "id": "faq_001",
            "question": "What is your refund policy?",
            "answer": "We offer full refunds within 30 days of purchase. After 30 days, partial refunds may be available depending on the product condition.",
            "category": "billing",
            "language": "en"
        },
        {
            "id": "faq_002",
            "question": "How long does shipping take?",
            "answer": "Standard shipping takes 5-7 business days. Express shipping takes 2-3 business days. International shipping varies by destination.",
            "category": "shipping",
            "language": "en"
        },
        {
            "id": "faq_003",
            "question": "Do you offer customer support?",
            "answer": "Yes, we offer 24/7 customer support via phone, email, and chat. Our team is always ready to assist you.",
            "category": "support",
            "language": "en"
        },
        {
            "id": "faq_004",
            "question": "Refund policy kya hai?",
            "answer": "Hum 30 din ke andar full refund dete hain. 30 din ke baad, product ki condition ke hisaab se partial refund ho sakta hai.",
            "category": "billing",
            "language": "ur"
        },
        {
            "id": "faq_005",
            "question": "Shipping mein kitna time lagta hai?",
            "answer": "Standard shipping mein 5-7 business days lagte hain. Express shipping 2-3 business days mein complete ho jata hai.",
            "category": "shipping",
            "language": "ur"
        }
    ],
    "policies": {
        "refund_policy": {
            "title": "Refund and Return Policy",
            "content": "Customers may request a full refund within 30 days of purchase. Products must be in original condition. After 30 days, refunds are subject to manager approval and may incur restocking fees.",
            "version": "1.2",
            "last_updated": "2024-01-15"
        },
        "privacy_policy": {
            "title": "Privacy Policy",
            "content": "We collect and process personal data solely for order fulfillment and customer support. Data is never sold to third parties. Customers may request data deletion at any time.",
            "version": "2.0",
            "last_updated": "2024-02-01"
        },
        "shipping_policy": {
            "title": "Shipping Policy",
            "content": "We ship to all 50 US states and internationally. Free standard shipping on orders over $50. Express shipping available for additional fee. Tracking provided for all orders.",
            "version": "1.5",
            "last_updated": "2024-01-20"
        }
    }
}


@mcp.tool()
async def search_faq(query: str, language: str = "en") -> dict:
    """
    Search company FAQs. Returns top 3 relevant answers.

    Args:
        query: The search query or question from the customer
        language: Language preference ('en' for English, 'ur' for Urdu)

    Returns:
        dict with status and matching FAQ results
    """
    try:
        logger.info(f"Searching FAQ for query: {query}, language: {language}")

        # Simple keyword matching (would use vector search in production)
        query_lower = query.lower()
        matches = []

        for faq in KNOWLEDGE_BASE["faq"]:
            if faq["language"] != language:
                continue

            # Check if query keywords match question or answer
            question_match = any(
                keyword in faq["question"].lower()
                for keyword in query_lower.split()
            )
            answer_match = any(
                keyword in faq["answer"].lower()
                for keyword in query_lower.split()
            )

            if question_match or answer_match:
                matches.append({
                    "id": faq["id"],
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "category": faq["category"],
                    "relevance_score": 1.0 if question_match else 0.8
                })

        # Sort by relevance and return top 3
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_matches = matches[:3]

        return {
            "status": "success",
            "data": {
                "query": query,
                "language": language,
                "results": top_matches,
                "total_matches": len(matches)
            }
        }

    except Exception as e:
        logger.error(f"Error searching FAQ: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "SEARCH_ERROR",
                "message": f"Failed to search FAQ: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_policy(policy_name: str) -> dict:
    """
    Fetch a specific policy document by name.

    Args:
        policy_name: Name of the policy (e.g., 'refund_policy', 'privacy_policy')

    Returns:
        dict with status and policy document contents
    """
    try:
        logger.info(f"Fetching policy: {policy_name}")

        policy = KNOWLEDGE_BASE["policies"].get(policy_name)

        if not policy:
            return {
                "status": "error",
                "error": {
                    "code": "POLICY_NOT_FOUND",
                    "message": f"Policy not found: {policy_name}",
                    "recoverable": True,
                    "available_policies": list(KNOWLEDGE_BASE["policies"].keys())
                }
            }

        return {
            "status": "success",
            "data": {
                "policy_name": policy_name,
                "title": policy["title"],
                "content": policy["content"],
                "version": policy["version"],
                "last_updated": policy["last_updated"]
            }
        }

    except Exception as e:
        logger.error(f"Error fetching policy: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "POLICY_ERROR",
                "message": f"Failed to fetch policy: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def list_available_policies() -> dict:
    """
    List all available policy documents.

    Returns:
        dict with status and list of policy names
    """
    try:
        logger.info("Listing available policies")

        policies = [
            {
                "name": key,
                "title": policy["title"],
                "version": policy["version"]
            }
            for key, policy in KNOWLEDGE_BASE["policies"].items()
        ]

        return {
            "status": "success",
            "data": {
                "policies": policies,
                "total_count": len(policies)
            }
        }

    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "LIST_ERROR",
                "message": f"Failed to list policies: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("MCP_SERVER_PORT", "8001"))

    logger.info(f"Starting Knowledge MCP Server on port {port}")

    # Run with SSE transport
    mcp.run(transport="sse", host="0.0.0.0", port=port)