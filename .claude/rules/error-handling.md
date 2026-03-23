# Error Handling - Structured Responses

All MCP tools must return structured response objects. Never raise raw exceptions.

**Success Pattern:**
```python
return {
    "status": "success",
    "data": {"key": "value"}
}
```

**Error Pattern:**
```python
return {
    "status": "error",
    "error": {
        "code": "NOT_FOUND",
        "message": "Policy not found: refund_policy",
        "recoverable": True
    }
}
```

**Rules:**
- Wrap all logic in try/except blocks
- Catch specific exceptions before generic Exception
- Log errors with full context before returning
- Set `recoverable` flag to guide agent escalation logic
- Never expose stack traces or internal errors to agents