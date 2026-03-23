"""
Escalation MCP Server - Route to human, send SMS/email alerts, PagerDuty integration

This server provides tools for escalating issues to human agents,
sending notifications, and creating urgent tickets.
"""

import os
import logging
from typing import Optional
from datetime import datetime
from enum import Enum

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("escalation-server")


class EscalationLevel(str, Enum):
    L1 = "l1"  # Frontline support
    L2 = "l2"  # Technical specialist
    L3 = "l3"  # Senior specialist
    MANAGER = "manager"  # Team lead/manager
    EXECUTIVE = "executive"  # Executive escalation


class NotificationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    SLACK = "slack"


# In-memory escalation database (would integrate with PagerDuty/Twilio in production)
ESCALATION_DATABASE = {
    "on_call_schedule": {
        "l1": [
            {"agent_id": "agent_001", "name": "Alice Johnson", "phone": "+1-555-0201", "email": "alice@support.com"},
            {"agent_id": "agent_002", "name": "Bob Smith", "phone": "+1-555-0202", "email": "bob@support.com"}
        ],
        "l2": [
            {"agent_id": "agent_003", "name": "Carol Williams", "phone": "+1-555-0203", "email": "carol@support.com"}
        ],
        "manager": [
            {"agent_id": "mgr_001", "name": "David Brown", "phone": "+1-555-0204", "email": "david@manager.com"}
        ]
    },
    "escalations": [
        {
            "id": "esc_001",
            "ticket_id": "tkt_002",
            "customer_id": "cust_002",
            "level": EscalationLevel.L2,
            "reason": "Complex billing dispute requiring specialist review",
            "status": "pending",
            "created_at": "2024-03-20T12:00:00Z",
            "assigned_to": "agent_003",
            "notifications_sent": ["sms", "email"]
        }
    ],
    "escalation_counter": 1
}


@mcp.tool()
async def route_to_human(
    customer_id: str,
    ticket_id: Optional[str] = None,
    reason: str = "",
    level: str = "l1",
    callback_number: Optional[str] = None
) -> dict:
    """
    Route a customer issue to a human agent.

    Args:
        customer_id: The customer ID
        ticket_id: Optional associated ticket ID
        reason: Reason for escalation
        level: Escalation level (l1, l2, l3, manager, executive)
        callback_number: Customer's callback number

    Returns:
        dict with status and escalation details
    """
    try:
        logger.info(f"Routing to human agent: customer={customer_id}, level={level}")

        ESCALATION_DATABASE["escalation_counter"] += 1
        escalation_id = f"esc_{ESCALATION_DATABASE['escalation_counter']:03d}"

        # Find on-call agent for the level
        on_call_agents = ESCALATION_DATABASE["on_call_schedule"].get(level.lower(), [])
        if not on_call_agents:
            return {
                "status": "error",
                "error": {
                    "code": "NO_AGENT_AVAILABLE",
                    "message": f"No on-call agents found for level: {level}",
                    "recoverable": True
                }
            }

        assigned_agent = on_call_agents[0]

        now = datetime.utcnow().isoformat() + "Z"

        new_escalation = {
            "id": escalation_id,
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "level": EscalationLevel(level.lower()),
            "reason": reason,
            "status": "pending",
            "created_at": now,
            "assigned_to": assigned_agent["agent_id"],
            "assigned_to_name": assigned_agent["name"],
            "callback_number": callback_number,
            "notifications_sent": []
        }

        ESCALATION_DATABASE["escalations"].append(new_escalation)

        # Send notifications to assigned agent
        notifications = []
        if assigned_agent.get("phone"):
            notifications.append("sms")
        if assigned_agent.get("email"):
            notifications.append("email")

        new_escalation["notifications_sent"] = notifications

        return {
            "status": "success",
            "data": {
                "escalation": new_escalation,
                "assigned_agent": assigned_agent,
                "message": f"Escalation {escalation_id} created, assigned to {assigned_agent['name']}",
                "notifications_sent": notifications
            }
        }

    except Exception as e:
        logger.error(f"Error routing to human: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ROUTE_ERROR",
                "message": f"Failed to route to human: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def send_sms_alert(
    recipient_phone: str,
    message: str,
    escalation_id: Optional[str] = None
) -> dict:
    """
    Send an SMS alert notification.

    Args:
        recipient_phone: Phone number to send SMS to
        message: Alert message content
        escalation_id: Optional associated escalation ID

    Returns:
        dict with status and SMS delivery details
    """
    try:
        logger.info(f"Sending SMS alert to: {recipient_phone}")

        # In production, this would integrate with Twilio
        # Twilio API call would go here
        sms_id = f"sms_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return {
            "status": "success",
            "data": {
                "sms_id": sms_id,
                "recipient_phone": recipient_phone,
                "message": message,
                "escalation_id": escalation_id,
                "sent_at": datetime.utcnow().isoformat() + "Z",
                "provider": "twilio",
                "message": "SMS alert sent successfully"
            }
        }

    except Exception as e:
        logger.error(f"Error sending SMS alert: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "SMS_ERROR",
                "message": f"Failed to send SMS alert: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def send_email_alert(
    recipient_email: str,
    subject: str,
    body: str,
    escalation_id: Optional[str] = None,
    priority: str = "normal"
) -> dict:
    """
    Send an email alert notification.

    Args:
        recipient_email: Email address to send to
        subject: Email subject
        body: Email body content
        escalation_id: Optional associated escalation ID
        priority: Email priority (low, normal, high, urgent)

    Returns:
        dict with status and email delivery details
    """
    try:
        logger.info(f"Sending email alert to: {recipient_email}")

        # In production, this would integrate with SendGrid/SES
        email_id = f"email_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return {
            "status": "success",
            "data": {
                "email_id": email_id,
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
                "escalation_id": escalation_id,
                "priority": priority,
                "sent_at": datetime.utcnow().isoformat() + "Z",
                "provider": "sendgrid",
                "message": "Email alert sent successfully"
            }
        }

    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "EMAIL_ERROR",
                "message": f"Failed to send email alert: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def trigger_pagerduty(
    incident_title: str,
    description: str,
    severity: str = "warning",
    customer_id: Optional[str] = None,
    ticket_id: Optional[str] = None
) -> dict:
    """
    Trigger a PagerDuty incident.

    Args:
        incident_title: Title of the incident
        description: Detailed description
        severity: Severity level (critical, error, warning, info)
        customer_id: Optional associated customer ID
        ticket_id: Optional associated ticket ID

    Returns:
        dict with status and PagerDuty incident details
    """
    try:
        logger.info(f"Triggering PagerDuty incident: {incident_title}")

        # In production, this would integrate with PagerDuty API
        pd_incident_id = f"pd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return {
            "status": "success",
            "data": {
                "incident_id": pd_incident_id,
                "title": incident_title,
                "description": description,
                "severity": severity,
                "customer_id": customer_id,
                "ticket_id": ticket_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "provider": "pagerduty",
                "status": "triggered",
                "message": "PagerDuty incident created"
            }
        }

    except Exception as e:
        logger.error(f"Error triggering PagerDuty: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "PAGERDUTY_ERROR",
                "message": f"Failed to trigger PagerDuty: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def create_urgent_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "urgent",
    requires_callback: bool = True,
    callback_number: Optional[str] = None
) -> dict:
    """
    Create an urgent ticket that requires immediate attention.

    Args:
        customer_id: The customer ID
        subject: Ticket subject
        description: Detailed description
        priority: Priority level (default: urgent)
        requires_callback: Whether customer callback is needed
        callback_number: Customer's callback number

    Returns:
        dict with status and created ticket details
    """
    try:
        logger.info(f"Creating urgent ticket for customer: {customer_id}")

        # Import ticketing tools if available (in production would call ticketing-mcp)
        # For now, create directly in the shared database
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Generate ticket ID
        ticket_id = f"tkt_urgent_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        now = datetime.utcnow().isoformat() + "Z"

        new_ticket = {
            "id": ticket_id,
            "customer_id": customer_id,
            "subject": subject,
            "description": description,
            "status": "open",
            "priority": priority,
            "created_at": now,
            "updated_at": now,
            "assigned_to": None,
            "tags": ["urgent", "escalation"],
            "requires_callback": requires_callback,
            "callback_number": callback_number
        }

        return {
            "status": "success",
            "data": {
                "ticket": new_ticket,
                "message": f"Urgent ticket {ticket_id} created",
                "next_step": "Ticket assigned to on-call specialist"
            }
        }

    except Exception as e:
        logger.error(f"Error creating urgent ticket: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "URGENT_TICKET_ERROR",
                "message": f"Failed to create urgent ticket: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_escalation_status(escalation_id: str) -> dict:
    """
    Get status of an escalation.

    Args:
        escalation_id: The escalation ID

    Returns:
        dict with status and escalation details
    """
    try:
        logger.info(f"Fetching escalation status: {escalation_id}")

        escalation = None
        for esc in ESCALATION_DATABASE["escalations"]:
            if esc["id"] == escalation_id:
                escalation = esc
                break

        if not escalation:
            return {
                "status": "error",
                "error": {
                    "code": "ESCALATION_NOT_FOUND",
                    "message": f"Escalation not found: {escalation_id}",
                    "recoverable": True
                }
            }

        return {
            "status": "success",
            "data": {
                "escalation": escalation
            }
        }

    except Exception as e:
        logger.error(f"Error fetching escalation status: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "STATUS_ERROR",
                "message": f"Failed to fetch escalation status: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8006"))
    logger.info(f"Starting Escalation MCP Server on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)