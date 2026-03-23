---
name: fastmcp-server-skill
description: Build MCP servers using FastMCP with proper error handling, async patterns, and structured responses
---

# FastMCP Server Skill

Build MCP servers using FastMCP for tool, resource, and prompt exposure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP Client (Agent)                              │
│           agents.mcp import MCPServerStreamableHttp                  │
└─────────────────────────────────────────────────────────────────────┘
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastMCP Server                                    │
│  @mcp.tool()    → Function tools                                    │
│  @mcp.resource() → Data resources                                   │
│  @mcp.prompt()   → Prompt templates                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
pip install fastmcp
# Or with uv
uv add fastmcp
```

### Basic Server

```python
from fastmcp import FastMCP
import os

mcp = FastMCP("my-mcp-server")

@mcp.tool()
async def search_faq(query: str, language: str = "en") -> dict:
    """Search the knowledge base for FAQs."""
    try:
        results = await db.search(query, language=language)
        return {
            "status": "success",
            "data": {
                "results": results,
                "total": len(results)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "SEARCH_FAILED",
                "message": str(e),
                "recoverable": True
            }
        }

@mcp.tool()
async def get_order_status(order_id: str) -> dict:
    """Get order status by order ID."""
    try:
        if not order_id:
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "Order ID is required",
                    "recoverable": False
                }
            }
        order = await orders.get(order_id)
        return {
            "status": "success",
            "data": {"order": order}
        }
    except NotFoundError:
        return {
            "status": "error",
            "error": {
                "code": "NOT_FOUND",
                "message": f"Order not found: {order_id}",
                "recoverable": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "recoverable": False
            }
        }
```

### Run Server

```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
```

## Error Handling Pattern

All MCP tools must return structured responses:

```python
# Success
return {
    "status": "success",
    "data": {...}
}

# Error with recovery guidance
return {
    "status": "error",
    "error": {
        "code": "ERROR_CODE",      # UPPER_SNAKE_CASE
        "message": "Human readable message",
        "recoverable": True/False  # Can agent retry?
    }
}
```

## Async Requirements

All tools must be `async def`. Never block the event loop:

```python
# GOOD
@mcp.tool()
async def search_faq(query: str) -> dict:
    results = await db.search(query)  # Await async DB call
    return {"status": "success", "data": results}

# BAD
@mcp.tool()
def search_faq(query: str) -> dict:
    results = db.search(query)  # Sync call - BLOCKS event loop
    return {"status": "success", "data": results}
```

## Tool Naming Conventions

| Pattern | Example |
|---------|---------|
| Actions | `search_faq`, `create_order`, `cancel_appointment` |
| Queries | `get_order_status`, `check_availability` |
| Updates | `update_customer`, `reschedule_appointment` |

## Resource Templates

```python
@mcp.resource("customer://{customer_id}")
async def get_customer_resource(customer_id: str) -> dict:
    """Expose customer data as a resource."""
    customer = await db.customers.get(customer_id)
    return {"customer": customer}

@mcp.resource("policy://{policy_name}")
async def get_policy_resource(policy_name: str) -> dict:
    """Expose policy documents."""
    policy = await db.policies.get(policy_name)
    return {"policy": policy}
```

## MCP Server Template

```python
"""
{MCP Server Name} - {Description}

Built with FastMCP. Provides tools for {use case}.
"""

import logging
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("{server-name}")

@mcp.tool()
async def {action}({params}) -> dict:
    """ {Description of what this tool does}. """
    try:
        # Implementation
        return {"status": "success", "data": {...}}
    except Exception as e:
        logger.error(f"{action} error: {str(e)}")
        return {
            "status": "error",
            "error": {
                "code": "{ERROR_CODE}",
                "message": str(e),
                "recoverable": True
            }
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=int(os.getenv("PORT", 8000)))
```

## Connecting to Agent

```python
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="{Server Name}",
    params={"url": "http://localhost:8000/api/mcp"},
    cache_tools_list=True,
) as mcp_server:
    agent = Agent(
        name="{Agent Name}",
        instructions="""...""",
        mcp_servers=[mcp_server],
    )
    result = await Runner.run(agent, "User query", config=config)
```
