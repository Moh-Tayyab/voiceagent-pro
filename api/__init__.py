"""
VoiceAgent Pro - API package

FastAPI application and routes.
"""

from api.main import app
from api.routes.voice import voice_router
from api.routes.agents import agents_router

__all__ = ["app", "voice_router", "agents_router"]