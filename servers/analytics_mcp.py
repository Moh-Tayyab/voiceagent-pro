"""
Analytics MCP Server - Log call outcomes, generate reports, track resolution rates

This server provides tools for analytics and reporting on call outcomes,
agent performance, and resolution metrics.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("analytics-server")


class CallOutcome(str, Enum):
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CALLBACK_REQUESTED = "callback_requested"
    NO_RESOLUTION = "no_resolution"
    ABANDONED = "abandoned"


# In-memory analytics database (would be PostgreSQL in production)
ANALYTICS_DATABASE = {
    "call_logs": [
        {
            "id": "call_001",
            "session_id": "sess_001",
            "customer_id": "cust_001",
            "timestamp": "2024-03-20T10:00:00Z",
            "duration_seconds": 180,
            "outcome": CallOutcome.RESOLVED,
            "language": "en",
            "agent_type": "faq_agent",
            "satisfaction_score": 5,
            "tags": ["billing", "refund"]
        },
        {
            "id": "call_002",
            "session_id": "sess_002",
            "customer_id": "cust_002",
            "timestamp": "2024-03-20T11:30:00Z",
            "duration_seconds": 420,
            "outcome": CallOutcome.ESCALATED,
            "language": "en",
            "agent_type": "triage_agent",
            "escalation_reason": "Complex billing issue",
            "tags": ["billing", "dispute"]
        },
        {
            "id": "call_003",
            "session_id": "sess_003",
            "customer_id": "cust_003",
            "timestamp": "2024-03-21T09:15:00Z",
            "duration_seconds": 240,
            "outcome": CallOutcome.RESOLVED,
            "language": "ur",
            "agent_type": "faq_agent",
            "satisfaction_score": 4,
            "tags": ["shipping", "tracking"]
        }
    ],
    "daily_stats": {
        "2024-03-20": {
            "total_calls": 2,
            "resolved": 1,
            "escalated": 1,
            "avg_duration": 300,
            "avg_satisfaction": 5.0
        },
        "2024-03-21": {
            "total_calls": 1,
            "resolved": 1,
            "escalated": 0,
            "avg_duration": 240,
            "avg_satisfaction": 4.0
        }
    }
}


@mcp.tool()
async def log_call_outcome(
    session_id: str,
    customer_id: str,
    outcome: str,
    duration_seconds: int,
    language: str = "en",
    agent_type: str = "triage_agent",
    satisfaction_score: Optional[int] = None,
    tags: Optional[list] = None,
    escalation_reason: Optional[str] = None,
    resolution_summary: Optional[str] = None
) -> dict:
    """
    Log the outcome of a call session.

    Args:
        session_id: Unique session identifier
        customer_id: The customer ID
        outcome: Call outcome (resolved, escalated, callback_requested, no_resolution, abandoned)
        duration_seconds: Call duration in seconds
        language: Language used (en, ur)
        agent_type: Type of agent that handled the call
        satisfaction_score: Optional 1-5 satisfaction score
        tags: Optional list of tags for categorization
        escalation_reason: Reason if escalated
        resolution_summary: Brief summary of resolution

    Returns:
        dict with status and logged call details
    """
    try:
        logger.info(f"Logging call outcome for session: {session_id}")

        call_id = f"call_{len(ANALYTICS_DATABASE['call_logs']) + 1:03d}"
        now = datetime.utcnow().isoformat() + "Z"

        call_log = {
            "id": call_id,
            "session_id": session_id,
            "customer_id": customer_id,
            "timestamp": now,
            "duration_seconds": duration_seconds,
            "outcome": CallOutcome(outcome.lower()),
            "language": language,
            "agent_type": agent_type,
            "satisfaction_score": satisfaction_score,
            "tags": tags or [],
            "escalation_reason": escalation_reason,
            "resolution_summary": resolution_summary
        }

        ANALYTICS_DATABASE["call_logs"].append(call_log)

        # Update daily stats
        today = now.split("T")[0]
        if today not in ANALYTICS_DATABASE["daily_stats"]:
            ANALYTICS_DATABASE["daily_stats"][today] = {
                "total_calls": 0,
                "resolved": 0,
                "escalated": 0,
                "avg_duration": 0,
                "avg_satisfaction": 0.0
            }

        daily = ANALYTICS_DATABASE["daily_stats"][today]
        daily["total_calls"] += 1
        if outcome.lower() == "resolved":
            daily["resolved"] += 1
        elif outcome.lower() == "escalated":
            daily["escalated"] += 1

        # Update averages
        today_calls = [c for c in ANALYTICS_DATABASE["call_logs"] if c["timestamp"].startswith(today)]
        daily["avg_duration"] = sum(c["duration_seconds"] for c in today_calls) // len(today_calls)
        scores = [c["satisfaction_score"] for c in today_calls if c["satisfaction_score"]]
        if scores:
            daily["avg_satisfaction"] = sum(scores) / len(scores)

        return {
            "status": "success",
            "data": {
                "call_log": call_log,
                "message": f"Call outcome logged for session {session_id}"
            }
        }

    except Exception as e:
        logger.error(f"Error logging call outcome: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "LOG_ERROR",
                "message": f"Failed to log call outcome: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_resolution_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_type: Optional[str] = None
) -> dict:
    """
    Get resolution statistics for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: last 7 days)
        end_date: End date in YYYY-MM-DD format (default: today)
        agent_type: Optional filter by agent type

    Returns:
        dict with status and resolution statistics
    """
    try:
        logger.info(f"Fetching resolution stats")

        # Default to last 7 days if not specified
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Filter call logs
        filtered_calls = [
            call for call in ANALYTICS_DATABASE["call_logs"]
            if start_date <= call["timestamp"].split("T")[0] <= end_date
        ]

        if agent_type:
            filtered_calls = [c for c in filtered_calls if c["agent_type"] == agent_type]

        if not filtered_calls:
            return {
                "status": "success",
                "data": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_calls": 0,
                    "resolution_rate": 0.0,
                    "message": "No calls found in date range"
                }
            }

        # Calculate stats
        total = len(filtered_calls)
        resolved = sum(1 for c in filtered_calls if c["outcome"] == CallOutcome.RESOLVED)
        escalated = sum(1 for c in filtered_calls if c["outcome"] == CallOutcome.ESCALATED)
        resolution_rate = (resolved / total) * 100 if total > 0 else 0

        avg_duration = sum(c["duration_seconds"] for c in filtered_calls) // total
        satisfaction_scores = [c["satisfaction_score"] for c in filtered_calls if c["satisfaction_score"]]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

        # Language breakdown
        language_counts = defaultdict(int)
        for call in filtered_calls:
            language_counts[call["language"]] += 1

        return {
            "status": "success",
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "total_calls": total,
                "resolved": resolved,
                "escalated": escalated,
                "resolution_rate": round(resolution_rate, 2),
                "avg_duration_seconds": avg_duration,
                "avg_satisfaction": round(avg_satisfaction, 2),
                "language_breakdown": dict(language_counts)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching resolution stats: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "STATS_ERROR",
                "message": f"Failed to fetch resolution stats: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def generate_report(
    report_type: str,
    start_date: str,
    end_date: str,
    group_by: Optional[str] = None
) -> dict:
    """
    Generate an analytics report.

    Args:
        report_type: Type of report (summary, agent_performance, language, outcome)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        group_by: Optional grouping (agent_type, language, outcome)

    Returns:
        dict with status and report data
    """
    try:
        logger.info(f"Generating {report_type} report")

        # Filter call logs
        filtered_calls = [
            call for call in ANALYTICS_DATABASE["call_logs"]
            if start_date <= call["timestamp"].split("T")[0] <= end_date
        ]

        if not filtered_calls:
            return {
                "status": "success",
                "data": {
                    "report_type": report_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "message": "No data for date range",
                    "rows": []
                }
            }

        # Group data if requested
        if group_by:
            grouped = defaultdict(list)
            for call in filtered_calls:
                if group_by in call:
                    grouped[call[group_by]].append(call)
            grouped_data = {k: list(v) for k, v in grouped.items()}
        else:
            grouped_data = {"all": filtered_calls}

        # Build report rows
        rows = []
        for group_key, calls in grouped_data.items():
            total = len(calls)
            resolved = sum(1 for c in calls if c["outcome"] == CallOutcome.RESOLVED)
            escalated = sum(1 for c in calls if c["outcome"] == CallOutcome.ESCALATED)
            avg_duration = sum(c["duration_seconds"] for c in calls) // total if total > 0 else 0
            satisfaction_scores = [c["satisfaction_score"] for c in calls if c["satisfaction_score"]]
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

            rows.append({
                "group": group_key,
                "total_calls": total,
                "resolved": resolved,
                "escalated": escalated,
                "resolution_rate": round((resolved / total) * 100, 2) if total > 0 else 0,
                "avg_duration_seconds": avg_duration,
                "avg_satisfaction": round(avg_satisfaction, 2)
            })

        return {
            "status": "success",
            "data": {
                "report_type": report_type,
                "start_date": start_date,
                "end_date": end_date,
                "group_by": group_by,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "rows": rows
            }
        }

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "REPORT_ERROR",
                "message": f"Failed to generate report: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_call_history(customer_id: str, limit: int = 10) -> dict:
    """
    Get call history for a specific customer.

    Args:
        customer_id: The customer ID
        limit: Maximum number of calls to return

    Returns:
        dict with status and call history
    """
    try:
        logger.info(f"Fetching call history for customer: {customer_id}")

        customer_calls = [
            call for call in ANALYTICS_DATABASE["call_logs"]
            if call["customer_id"] == customer_id
        ]

        # Sort by timestamp descending and apply limit
        customer_calls.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_calls = customer_calls[:limit]

        return {
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "calls": recent_calls,
                "total_calls": len(customer_calls)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching call history: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "HISTORY_ERROR",
                "message": f"Failed to fetch call history: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8005"))
    logger.info(f"Starting Analytics MCP Server on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)