"""
Calendar MCP Server - Appointment booking, availability checks, rescheduling

This server provides tools for managing appointments including
checking availability, booking, and rescheduling.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("calendar-server")


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


# In-memory calendar database (would be Google Calendar in production)
CALENDAR_DATABASE = {
    "appointments": {
        "apt_001": {
            "id": "apt_001",
            "customer_id": "cust_001",
            "customer_name": "John Smith",
            "customer_email": "john.smith@example.com",
            "customer_phone": "+1-555-0101",
            "service_type": "Product Demo",
            "scheduled_at": "2024-03-25T14:00:00Z",
            "duration_minutes": 30,
            "status": AppointmentStatus.CONFIRMED,
            "notes": "First-time customer demo",
            "created_at": "2024-03-20T10:00:00Z"
        },
        "apt_002": {
            "id": "apt_002",
            "customer_id": "cust_002",
            "customer_name": "Sarah Ahmed",
            "customer_email": "sarah.ahmed@example.com",
            "customer_phone": "+1-555-0102",
            "service_type": "Technical Support",
            "scheduled_at": "2024-03-26T10:00:00Z",
            "duration_minutes": 60,
            "status": AppointmentStatus.PENDING,
            "notes": "Follow-up on ticket tkt_002",
            "created_at": "2024-03-21T09:00:00Z"
        }
    },
    "available_slots": {
        "2024-03-24": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
        "2024-03-25": ["09:00", "11:00", "15:00", "16:00"],  # 14:00 booked
        "2024-03-26": ["11:00", "14:00", "15:00", "16:00"],  # 10:00 booked
        "2024-03-27": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
        "2024-03-28": ["09:00", "10:00", "14:00", "15:00", "16:00"]
    },
    "service_types": ["Product Demo", "Technical Support", "Onboarding", "Consultation", "Training"]
}


@mcp.tool()
async def check_availability(
    date: str,
    service_type: Optional[str] = None,
    duration_minutes: int = 30
) -> dict:
    """
    Check available time slots for a given date.

    Args:
        date: Date in YYYY-MM-DD format
        service_type: Type of service being requested
        duration_minutes: Required duration in minutes

    Returns:
        dict with status and available time slots
    """
    try:
        logger.info(f"Checking availability for date: {date}")

        # Get available slots for the date
        slots = CALENDAR_DATABASE["available_slots"].get(date, [])

        if not slots:
            return {
                "status": "error",
                "error": {
                    "code": "NO_AVAILABILITY",
                    "message": f"No available slots for date: {date}",
                    "recoverable": True,
                    "suggested_dates": list(CALENDAR_DATABASE["available_slots"].keys())[:3]
                }
            }

        return {
            "status": "success",
            "data": {
                "date": date,
                "available_slots": slots,
                "service_type": service_type,
                "duration_minutes": duration_minutes,
                "slot_count": len(slots)
            }
        }

    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "AVAILABILITY_ERROR",
                "message": f"Failed to check availability: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def book_appointment(
    customer_id: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    date: str,
    time: str,
    service_type: str,
    duration_minutes: int = 30,
    notes: Optional[str] = None
) -> dict:
    """
    Book a new appointment.

    Args:
        customer_id: The customer ID
        customer_name: Customer full name
        customer_email: Customer email address
        customer_phone: Customer phone number
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        service_type: Type of service
        duration_minutes: Duration in minutes
        notes: Optional notes for the appointment

    Returns:
        dict with status and appointment details
    """
    try:
        logger.info(f"Booking appointment for {customer_name} on {date} at {time}")

        # Generate appointment ID
        apt_number = len(CALENDAR_DATABASE["appointments"]) + 1
        appointment_id = f"apt_{apt_number:03d}"

        # Construct datetime
        scheduled_at = f"{date}T{time}:00Z"

        new_appointment = {
            "id": appointment_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "service_type": service_type,
            "scheduled_at": scheduled_at,
            "duration_minutes": duration_minutes,
            "status": AppointmentStatus.CONFIRMED,
            "notes": notes or "",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        CALENDAR_DATABASE["appointments"][appointment_id] = new_appointment

        # Remove booked slot from availability
        if date in CALENDAR_DATABASE["available_slots"]:
            if time in CALENDAR_DATABASE["available_slots"][date]:
                CALENDAR_DATABASE["available_slots"][date].remove(time)

        return {
            "status": "success",
            "data": {
                "appointment": new_appointment,
                "message": f"Appointment {appointment_id} confirmed for {date} at {time}",
                "confirmation_sent_to": customer_email
            }
        }

    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "BOOKING_ERROR",
                "message": f"Failed to book appointment: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str,
    reason: Optional[str] = None
) -> dict:
    """
    Reschedule an existing appointment.

    Args:
        appointment_id: The appointment ID to reschedule
        new_date: New date in YYYY-MM-DD format
        new_time: New time in HH:MM format
        reason: Optional reason for rescheduling

    Returns:
        dict with status and updated appointment details
    """
    try:
        logger.info(f"Rescheduling appointment: {appointment_id} to {new_date} {new_time}")

        appointment = CALENDAR_DATABASE["appointments"].get(appointment_id)

        if not appointment:
            return {
                "status": "error",
                "error": {
                    "code": "APPOINTMENT_NOT_FOUND",
                    "message": f"Appointment not found: {appointment_id}",
                    "recoverable": True
                }
            }

        # Store old datetime for reference
        old_scheduled_at = appointment["scheduled_at"]

        # Update appointment
        appointment["scheduled_at"] = f"{new_date}T{new_time}:00Z"
        appointment["updated_at"] = datetime.utcnow().isoformat() + "Z"

        if reason:
            appointment["notes"] += f"\n[Rescheduled]: {reason}"

        # Return old slot to availability
        old_date = old_scheduled_at.split("T")[0]
        old_time = old_scheduled_at.split("T")[1].split(":")[0] + ":" + old_scheduled_at.split("T")[1].split(":")[1]
        if old_date in CALENDAR_DATABASE["available_slots"]:
            if old_time not in CALENDAR_DATABASE["available_slots"][old_date]:
                CALENDAR_DATABASE["available_slots"][old_date].append(old_time)

        # Remove new slot from availability
        if new_date in CALENDAR_DATABASE["available_slots"]:
            if new_time in CALENDAR_DATABASE["available_slots"][new_date]:
                CALENDAR_DATABASE["available_slots"][new_date].remove(new_time)

        return {
            "status": "success",
            "data": {
                "appointment": appointment,
                "message": f"Appointment rescheduled from {old_scheduled_at} to {new_date}T{new_time}:00Z",
                "confirmation_sent_to": appointment["customer_email"]
            }
        }

    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "RESCHEDULE_ERROR",
                "message": f"Failed to reschedule appointment: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def cancel_appointment(appointment_id: str, reason: Optional[str] = None) -> dict:
    """
    Cancel an existing appointment.

    Args:
        appointment_id: The appointment ID to cancel
        reason: Optional reason for cancellation

    Returns:
        dict with status and cancellation details
    """
    try:
        logger.info(f"Cancelling appointment: {appointment_id}")

        appointment = CALENDAR_DATABASE["appointments"].get(appointment_id)

        if not appointment:
            return {
                "status": "error",
                "error": {
                    "code": "APPOINTMENT_NOT_FOUND",
                    "message": f"Appointment not found: {appointment_id}",
                    "recoverable": True
                }
            }

        # Update appointment status
        appointment["status"] = AppointmentStatus.CANCELLED
        appointment["cancelled_at"] = datetime.utcnow().isoformat() + "Z"

        if reason:
            appointment["notes"] += f"\n[Cancelled]: {reason}"

        # Return slot to availability
        date = appointment["scheduled_at"].split("T")[0]
        time = appointment["scheduled_at"].split("T")[1].split(":")[0] + ":" + appointment["scheduled_at"].split("T")[1].split(":")[1]
        if date in CALENDAR_DATABASE["available_slots"]:
            time_only = time.split(":")[0] + ":" + time.split(":")[1]
            if time_only not in CALENDAR_DATABASE["available_slots"][date]:
                CALENDAR_DATABASE["available_slots"][date].append(time_only)

        return {
            "status": "success",
            "data": {
                "appointment": appointment,
                "message": f"Appointment {appointment_id} cancelled",
                "cancellation_sent_to": appointment["customer_email"]
            }
        }

    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "CANCEL_ERROR",
                "message": f"Failed to cancel appointment: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_appointment(appointment_id: str) -> dict:
    """
    Get details of a specific appointment.

    Args:
        appointment_id: The appointment ID

    Returns:
        dict with status and appointment details
    """
    try:
        logger.info(f"Fetching appointment: {appointment_id}")

        appointment = CALENDAR_DATABASE["appointments"].get(appointment_id)

        if not appointment:
            return {
                "status": "error",
                "error": {
                    "code": "APPOINTMENT_NOT_FOUND",
                    "message": f"Appointment not found: {appointment_id}",
                    "recoverable": True
                }
            }

        return {
            "status": "success",
            "data": {
                "appointment": appointment
            }
        }

    except Exception as e:
        logger.error(f"Error fetching appointment: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "GET_APPOINTMENT_ERROR",
                "message": f"Failed to fetch appointment: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_customer_appointments(customer_id: str, status_filter: Optional[str] = None) -> dict:
    """
    Get all appointments for a customer.

    Args:
        customer_id: The customer ID
        status_filter: Optional status to filter by (pending, confirmed, cancelled, completed)

    Returns:
        dict with status and list of appointments
    """
    try:
        logger.info(f"Fetching appointments for customer: {customer_id}")

        customer_appointments = [
            apt for apt in CALENDAR_DATABASE["appointments"].values()
            if apt["customer_id"] == customer_id
        ]

        if status_filter:
            customer_appointments = [
                a for a in customer_appointments
                if a["status"].value == status_filter.lower()
            ]

        # Sort by scheduled_at descending
        customer_appointments.sort(key=lambda x: x["scheduled_at"], reverse=True)

        return {
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "appointments": customer_appointments,
                "total_count": len(customer_appointments)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching customer appointments: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "GET_APPOINTMENTS_ERROR",
                "message": f"Failed to fetch appointments: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8004"))
    logger.info(f"Starting Calendar MCP Server on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)