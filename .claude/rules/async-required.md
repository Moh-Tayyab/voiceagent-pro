# Async Required

All FastAPI routes and MCP tools must be async using asyncio.

**FastAPI Route Pattern:**
```python
@app.post("/inbound")
async def handle_inbound(request: InboundRequest):
    result = await process_call(request)
    return result
```

**MCP Tool Pattern:**
```python
@mcp.tool()
async def search_faq(query: str, language: str = "en") -> dict:
    results = await db.search(query)
    return {"status": "success", "data": results}
```

**Rules:**
- Use `async def` for all route handlers and MCP tools
- Await all async operations (database, API calls, file I/O)
- Never block the event loop with synchronous operations
- Use `asyncio.gather()` for parallel async operations