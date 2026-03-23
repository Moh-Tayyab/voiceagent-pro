# Never Hardcode Secrets

All secrets must be loaded from environment variables only.

- API keys (Anthropic, OpenAI, Twilio, Deepgram, ElevenLabs)
- Database credentials (PostgreSQL, Redis)
- Webhook secrets
- Any authentication tokens

**Pattern:**
```python
import os

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

**Never:**
```python
API_KEY = "sk-..."  # FORBIDDEN
```
