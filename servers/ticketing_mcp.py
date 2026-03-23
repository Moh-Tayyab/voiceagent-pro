"""
Ticketing MCP Server - Create, update, escalate support tickets

This server provides tools for managing support tickets including
creation, updates, status changes, and escalation.
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
mcp = FastMCP("ticketing-server")


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# In-memory ticket database (would be Zendesk/Freshdesk in production)
TICKET_DATABASE = {
    "tickets": {
        "tkt_001": {
            "id": "tkt_001",
            "customer_id": "cust_001",
            "subject": "Product not working as expected",
            "description": "The widget I received is not functioning properly. Need assistance.",
            "status": TicketStatus.IN_PROGRESS,
            "priority": TicketPriority.MEDIUM,
            "created_at": "2024-03-15T10:00:00Z",
            "updated_at": "2024-03-16T14:30:00Z",
            "assigned_to": "agent_001",
            "tags": ["product_issue", "technical"]
        },
        "tkt_002": {
            "id": "tkt_002",
            "customer_id": "cust_002",
            "subject": "Billing discrepancy",
            "description": "I was charged twice for my subscription this month.",
            "status": TicketStatus.OPEN,
            "priority": TicketPriority.HIGH,
            "created_at": "2024-03-20T09:15:00Z",
            "updated_at": "2024-03-20T09:15:00Z",
            "assigned_to": None,
            "tags": ["billing", "urgent"]
        },
        "tkt_003": {
            "id": "tkt_003",
            "customer_id": "cust_003",
            "subject": "Feature request",
            "description": "Would like to see bulk export functionality added.",
            "status": TicketStatus.RESOLVED,
            "priority": TicketPriority.LOW,
            "created_at": "2024-03-10T11:00:00Z",
            "updated_at": "2024-03-12T16:00:00Z",
            "resolved_at": "2024-03-12T16:00:00Z",
            "assigned_to": "agent_002",
            "tags": ["feature_request"],
            "resolution": "Feature added to roadmap for Q2 release"
        }
    },
    "ticket_counter": 3
}


@mcp.tool()
async def create_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "medium",
    tags: Optional[list] = None
) -> dict:
    """
    Create a new support ticket.

    Args:
        customer_id: The customer ID
        subject: Ticket subject/summary
        description: Detailed description of the issue
        priority: Priority level (low, medium, high, urgent)
        tags: Optional list of tags for categorization

    Returns:
        dict with status and created ticket details
    """
    try:
        logger.info(f"Creating ticket for customer {customer_id}: {subject}")

        TICKET_DATABASE["ticket_counter"] += 1
        ticket_id = f"tkt_{TICKET_DATABASE['ticket_counter']:03d}"

        now = datetime.utcnow().isoformat() + "Z"

        new_ticket = {
            "id": ticket_id,
            "customer_id": customer_id,
            "subject": subject,
            "description": description,
            "status": TicketStatus.OPEN,
            "priority": TicketPriority(priority.lower()),
            "created_at": now,
            "updated_at": now,
            "assigned_to": None,
            "tags": tags or []
        }

        TICKET_DATABASE["tickets"][ticket_id] = new_ticket

        return {
            "status": "success",
            "data": {
                "ticket": new_ticket,
                "message": f"Ticket {ticket_id} created successfully"
            }
        }

    except Exception as e:
        logger.error(f"Error creating ticket: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "CREATE_TICKET_ERROR",
                "message": f"Failed to create ticket: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def update_ticket(
    ticket_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None
) -> dict:
    """
    Update an existing ticket.

    Args:
        ticket_id: The ticket ID to update
        status: New status (open, in_progress, pending_customer, resolved, closed)
        priority: New priority level
        description: Additional description/notes
        assigned_to: Agent ID to assign ticket to

    Returns:
        dict with status and updated ticket details
    """
    try:
        logger.info(f"Updating ticket: {ticket_id}")

        ticket = TICKET_DATABASE["tickets"].get(ticket_id)

        if not ticket:
            return {
                "status": "error",
                "error": {
                    "code": "TICKET_NOT_FOUND",
                    "message": f"Ticket not found: {ticket_id}",
                    "recoverable": True
                }
            }

        # Update fields if provided
        if status:
            ticket["status"] = TicketStatus(status.lower())
            if status.lower() == "resolved":
                ticket["resolved_at"] = datetime.utcnow().isoformat() + "Z"
        if priority:
            ticket["priority"] = TicketPriority(priority.lower())
        if description:
            ticket["description"] += f"\n\n[Update]: {description}"
        if assigned_to:
            ticket["assigned_to"] = assigned_to

        ticket["updated_at"] = datetime.utcnow().isoformat() + "Z"

        return {
            "status": "success",
            "data": {
                "ticket": ticket,
                "message": f"Ticket {ticket_id} updated successfully"
            }
        }

    except Exception as e:
        logger.error(f"Error updating ticket: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "UPDATE_TICKET_ERROR",
                "message": f"Failed to update ticket: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def escalate_ticket(ticket_id: str, reason: str, new_priority: str = "urgent") -> dict:
    """
    Escalate a ticket to higher priority or different team.

    Args:
        ticket_id: The ticket ID to escalate
        reason: Reason for escalation
        new_priority: New priority level (default: urgent)

    Returns:
        dict with status and escalation details
    """
    try:
        logger.info(f"Escalating ticket: {ticket_id}, reason: {reason}")

        ticket = TICKET_DATABASE["tickets"].get(ticket_id)

        if not ticket:
            return {
                "status": "error",
                "error": {
                    "code": "TICKET_NOT_FOUND",
                    "message": f"Ticket not found: {ticket_id}",
                    "recoverable": True
                }
            }

        # Update priority and add escalation note
        ticket["priority"] = TicketPriority(new_priority.lower())
        ticket["description"] += f"\n\n[ESCALATION]: {reason}"
        ticket["escalated_at"] = datetime.utcnow().isoformat() + "Z"
        ticket["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Add escalation tag
        if "escalated" not in ticket["tags"]:
            ticket["tags"].append("escalated")

        return {
            "status": "success",
            "data": {
                "ticket": ticket,
                "message": f"Ticket {ticket_id} escalated to {new_priority} priority",
                "escalation_reason": reason
            }
        }

    except Exception as e:
        logger.error(f"Error escalating ticket: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ESCALATE_TICKET_ERROR",
                "message": f"Failed to escalate ticket: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_ticket(ticket_id: str) -> dict:
    """
    Get details of a specific ticket.

    Args:
        ticket_id: The ticket ID

    Returns:
        dict with status and ticket details
    """
    try:
        logger.info(f"Fetching ticket: {ticket_id}")

        ticket = TICKET_DATABASE["tickets"].get(ticket_id)

        if not ticket:
            return {
                "status": "error",
                "error": {
                    "code": "TICKET_NOT_FOUND",
                    "message": f"Ticket not found: {ticket_id}",
                    "recoverable": True
                }
            }

        return {
            "status": "success",
            "data": {
                "ticket": ticket
            }
        }

    except Exception as e:
        logger.error(f"Error fetching ticket: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "GET_TICKET_ERROR",
                "message": f"Failed to fetch ticket: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_customer_tickets(customer_id: str, status_filter: Optional[str] = None) -> dict:
    """
    Get all tickets for a customer, optionally filtered by status.

    Args:
        customer_id: The customer ID
        status_filter: Optional status to filter by

    Returns:
        dict with status and list of tickets
    """
    try:
        logger.info(f"Fetching tickets for customer: {customer_id}")

        customer_tickets = [
            ticket for ticket in TICKET_DATABASE["tickets"].values()
            if ticket["customer_id"] == customer_id
        ]

        if status_filter:
            customer_tickets = [
                t for t in customer_tickets
                if t["status"].value == status_filter.lower()
            ]

        # Sort by updated_at descending
        customer_tickets.sort(key=lambda x: x["updated_at"], reverse=True)

        return {
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "tickets": customer_tickets,
                "total_count": len(customer_tickets)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching customer tickets: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "GET_TICKETS_ERROR",
                "message": f"Failed to fetch tickets: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8003"))
    logger.info(f"Starting Ticketing MCP Server on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)