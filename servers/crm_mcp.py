"""
CRM MCP Server - Customer lookup, history, account info

This server provides tools for accessing customer relationship management
data including customer profiles, order history, and account information.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("crm-server")

# In-memory CRM database (would be external CRM API in production)
CRM_DATABASE = {
    "customers": {
        "cust_001": {
            "id": "cust_001",
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "+1-555-0101",
            "created_at": "2024-01-15T10:30:00Z",
            "tier": "premium",
            "language_preference": "en"
        },
        "cust_002": {
            "id": "cust_002",
            "name": "Sarah Ahmed",
            "email": "sarah.ahmed@example.com",
            "phone": "+1-555-0102",
            "created_at": "2024-02-20T14:45:00Z",
            "tier": "standard",
            "language_preference": "en"
        },
        "cust_003": {
            "id": "cust_003",
            "name": "Muhammad Khan",
            "email": "muhammad.khan@example.com",
            "phone": "+92-300-1234567",
            "created_at": "2024-03-01T09:00:00Z",
            "tier": "premium",
            "language_preference": "ur"
        }
    },
    "orders": {
        "ord_001": {
            "id": "ord_001",
            "customer_id": "cust_001",
            "product": "Premium Widget",
            "amount": 299.99,
            "status": "delivered",
            "order_date": "2024-03-10T08:00:00Z",
            "delivery_date": "2024-03-15T16:00:00Z"
        },
        "ord_002": {
            "id": "ord_002",
            "customer_id": "cust_001",
            "product": "Standard Gadget",
            "amount": 149.99,
            "status": "shipped",
            "order_date": "2024-03-18T11:30:00Z",
            "estimated_delivery": "2024-03-25T16:00:00Z",
            "tracking_number": "TRK123456789"
        },
        "ord_003": {
            "id": "ord_003",
            "customer_id": "cust_002",
            "product": "Basic Plan Subscription",
            "amount": 49.99,
            "status": "active",
            "order_date": "2024-02-20T14:45:00Z",
            "renewal_date": "2024-04-20T14:45:00Z"
        },
        "ord_004": {
            "id": "ord_004",
            "customer_id": "cust_003",
            "product": "Enterprise Package",
            "amount": 999.99,
            "status": "processing",
            "order_date": "2024-03-20T09:00:00Z",
            "estimated_delivery": "2024-03-28T16:00:00Z"
        }
    },
    "accounts": {
        "acct_001": {
            "id": "acct_001",
            "customer_id": "cust_001",
            "balance": 0.00,
            "credit_limit": 5000.00,
            "payment_method": "credit_card",
            "auto_pay": True,
            "status": "active"
        },
        "acct_002": {
            "id": "acct_002",
            "customer_id": "cust_002",
            "balance": 49.99,
            "credit_limit": 1000.00,
            "payment_method": "bank_transfer",
            "auto_pay": False,
            "status": "active"
        },
        "acct_003": {
            "id": "acct_003",
            "customer_id": "cust_003",
            "balance": 0.00,
            "credit_limit": 10000.00,
            "payment_method": "invoice",
            "auto_pay": False,
            "status": "active"
        }
    }
}


@mcp.tool()
async def customer_lookup(identifier: str, identifier_type: str = "email") -> dict:
    """
    Look up a customer by email, phone, or customer ID.

    Args:
        identifier: The customer identifier (email, phone, or ID)
        identifier_type: Type of identifier ('email', 'phone', 'customer_id')

    Returns:
        dict with status and customer data
    """
    try:
        logger.info(f"Looking up customer by {identifier_type}: {identifier}")

        for customer in CRM_DATABASE["customers"].values():
            if identifier_type == "email" and customer["email"] == identifier:
                return {
                    "status": "success",
                    "data": {
                        "customer": customer,
                        "account": CRM_DATABASE["accounts"].get(customer["id"]),
                        "lookup_type": "email"
                    }
                }
            elif identifier_type == "phone" and customer["phone"] == identifier:
                return {
                    "status": "success",
                    "data": {
                        "customer": customer,
                        "account": CRM_DATABASE["accounts"].get(customer["id"]),
                        "lookup_type": "phone"
                    }
                }
            elif identifier_type == "customer_id" and customer["id"] == identifier:
                return {
                    "status": "success",
                    "data": {
                        "customer": customer,
                        "account": CRM_DATABASE["accounts"].get(customer["id"]),
                        "lookup_type": "customer_id"
                    }
                }

        return {
            "status": "error",
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": f"No customer found with {identifier_type}: {identifier}",
                "recoverable": True
            }
        }

    except Exception as e:
        logger.error(f"Error looking up customer: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "LOOKUP_ERROR",
                "message": f"Failed to look up customer: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_order_history(customer_id: str, limit: int = 10) -> dict:
    """
    Get order history for a customer.

    Args:
        customer_id: The customer ID
        limit: Maximum number of orders to return

    Returns:
        dict with status and order history
    """
    try:
        logger.info(f"Fetching order history for customer: {customer_id}")

        customer_orders = [
            order for order in CRM_DATABASE["orders"].values()
            if order["customer_id"] == customer_id
        ]

        # Sort by order date descending and apply limit
        customer_orders.sort(key=lambda x: x["order_date"], reverse=True)
        recent_orders = customer_orders[:limit]

        return {
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "orders": recent_orders,
                "total_orders": len(customer_orders),
                "returned_count": len(recent_orders)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching order history: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ORDER_HISTORY_ERROR",
                "message": f"Failed to fetch order history: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_account_info(customer_id: str) -> dict:
    """
    Get account information for a customer.

    Args:
        customer_id: The customer ID

    Returns:
        dict with status and account information
    """
    try:
        logger.info(f"Fetching account info for customer: {customer_id}")

        account = None
        for acct in CRM_DATABASE["accounts"].values():
            if acct["customer_id"] == customer_id:
                account = acct
                break

        if not account:
            return {
                "status": "error",
                "error": {
                    "code": "ACCOUNT_NOT_FOUND",
                    "message": f"No account found for customer: {customer_id}",
                    "recoverable": True
                }
            }

        return {
            "status": "success",
            "data": {
                "account": account,
                "customer_id": customer_id
            }
        }

    except Exception as e:
        logger.error(f"Error fetching account info: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ACCOUNT_ERROR",
                "message": f"Failed to fetch account info: {str(e)}",
                "recoverable": True
            }
        }


@mcp.tool()
async def get_order_status(order_id: str) -> dict:
    """
    Get status of a specific order.

    Args:
        order_id: The order ID

    Returns:
        dict with status and order details
    """
    try:
        logger.info(f"Fetching order status for: {order_id}")

        order = CRM_DATABASE["orders"].get(order_id)

        if not order:
            return {
                "status": "error",
                "error": {
                    "code": "ORDER_NOT_FOUND",
                    "message": f"Order not found: {order_id}",
                    "recoverable": True
                }
            }

        # Add customer name for context
        customer = CRM_DATABASE["customers"].get(order["customer_id"])
        order_with_customer = dict(order)
        order_with_customer["customer_name"] = customer["name"] if customer else "Unknown"

        return {
            "status": "success",
            "data": {
                "order": order_with_customer
            }
        }

    except Exception as e:
        logger.error(f"Error fetching order status: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "ORDER_STATUS_ERROR",
                "message": f"Failed to fetch order status: {str(e)}",
                "recoverable": True
            }
        }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8002"))
    logger.info(f"Starting CRM MCP Server on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)