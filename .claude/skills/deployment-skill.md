---
name: deployment-skill
description: Docker and Railway deployment configuration for VoiceAgent Pro
---

# Deployment Skill

Deploy VoiceAgent Pro to Railway with Docker.

## Project Structure

```
voiceagent-pro/
├── api/
│   └── main.py              # FastAPI application
├── servers/
│   ├── mcp_server.py        # FastMCP server
│   └── ...
├── agents/                   # Agent implementations
├── voice/                    # Voice processing
├── Dockerfile.api           # FastAPI container
├── Dockerfile.mcp           # MCP server container
├── docker-compose.yml       # Local development
└── railway.json            # Railway configuration
```

## Docker Configuration

### Dockerfile.api

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy requirements first for caching
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.mcp

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

ENV PORT=8001
ENV PYTHONUNBUFFERED=1

CMD ["python", "servers/mcp_server.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
    depends_on:
      - redis

  mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Local development only
  ngrok:
    image: wernight/ngrok
    ports:
      - "4040:4040"
    environment:
      - NGROK_AUTH_TOKEN=${NGROK_AUTH_TOKEN}
```

## Railway Configuration

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.api"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30
  }
}
```

### Alternative: railway.toml

```toml
[build]
builder = "DOCKERFILE"
dockerfile = "Dockerfile.api"

[deploy]
numReplicas = 1
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[healthcheck]]
path = "/health"
timeout = 30
interval = 15
```

## Environment Variables

Required for production:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection | `redis://host:6379` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `...` |
| `DEEPGRAM_API_KEY` | Deepgram STT key | `...` |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key | `...` |
| `MCP_SERVER_URL` | MCP server URL | `https://api.example.com/mcp` |

## Deployment Steps

### 1. Prepare Repository

```bash
# Ensure Dockerfile.api exists and is correct
# Ensure .dockerignore exists
cat > .dockerignore << EOF
.venv
.git
*.pyc
__pycache__
.env
.env.*
tests/
*.md
EOF

# Push to GitHub
git add .
git commit -m "Add Docker configuration"
git push
```

### 2. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project (if applicable)
railway link

# Add environment variables
railway variables set DATABASE_URL="postgresql://..."
railway variables set REDIS_URL="redis://..."
railway variables set ANTHROPIC_API_KEY="sk-ant-..."
# ... add other variables

# Deploy
railway up

# Get public URL
railway domain
```

### 3. Configure Twilio Webhook

```
Dashboard → Phone Numbers → Manage → Active Numbers → [Number]
  ↓
Voice Configuration
  ↓
WHEN A CALL COMES IN: https://your-api.railway.app/inbound
  ↓
HTTP Method: POST
```

### 4. Verify Deployment

```bash
# Check logs
railway logs

# Check health
curl https://your-api.railway.app/health

# Test with sample query
curl -X POST https://your-api.railway.app/inbound \
  -H "Content-Type: application/json" \
  -d '{"call_sid": "test", "from_number": "+1234567890", "transcription": "Hello"}'
```

## Local Development

```bash
# Start all services
docker-compose up --build

# Start only API
docker-compose up api

# View logs
docker-compose logs -f api

# Run tests
docker-compose exec api pytest tests/
```

## Troubleshooting

### Container Won't Start

```bash
# Check build logs
railway logs --build

# Common issues:
# - Missing environment variables
# - Port already in use
# - Python version mismatch
```

### Health Check Fails

```python
# Ensure /health endpoint exists and returns 200
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Database Connection Fails

```python
# Use async SQLAlchemy with connection pooling
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)
```

### MCP Server Connection Issues

```bash
# Verify MCP server is running
curl http://localhost:8001/health

# Check MCP endpoint
curl http://localhost:8001/api/mcp/tools
```
