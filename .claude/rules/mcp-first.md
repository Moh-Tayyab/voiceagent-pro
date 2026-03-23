# MCP First - All External Calls Through MCP

All external API calls must go through MCP servers. Never make direct HTTP calls from agent logic.

**Allowed:**
```python
# Agent calls MCP tool
result = await knowledge_mcp.search_faq(query="refund policy")
```

**Forbidden:**
```python
# Direct API call from agent - NEVER DO THIS
response = await httpx.post("https://api.zendesk.com/...")
```

**Rationale:**
- Keeps system modular and swappable per client
- Enables testing and isolation
- Centralizes error handling and logging