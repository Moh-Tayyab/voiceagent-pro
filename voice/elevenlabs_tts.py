"""
ElevenLabs TTS Handler - Text-to-speech synthesis

Handles voice synthesis using ElevenLabs API.
"""

import os
import logging
import asyncio
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    """
    ElevenLabs Text-to-Speech handler.

    Supports multiple voices and languages.
    """

    # Default voice IDs
    VOICES = {
        "default": "Rachel",  # Clear, professional female voice
        "male": "Josh",  # Professional male voice
        "friendly": "Dorothy",  # Warm, friendly voice
        "urdu": "Charlotte"  # Supports multiple languages
    }

    API_BASE = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")

        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            raise ValueError("ElevenLabs API key required")

        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "default",
        language: str = "en",
        speed: float = 1.0,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> dict:
        """
        Synthesize speech from text using ElevenLabs API.

        Args:
            text: Text to synthesize
            voice: Voice name or ID
            language: Language code
            speed: Speech speed (0.5 - 2.0)
            stability: Voice stability (0.0 - 1.0)
            similarity_boost: Similarity boost (0.0 - 1.0)

        Returns:
            Dict with audio data (base64), format, and duration
        """
        try:
            logger.debug(f"Synthesizing speech: {len(text)} chars")

            # Resolve voice ID
            voice_id = self._get_voice_id(voice)

            # Prepare request
            url = f"{self.API_BASE}/text-to-speech/{voice_id}"

            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "speed": speed
                }
            }

            # Make request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )

                if response.status_code == 200:
                    # Return audio bytes as base64
                    import base64
                    audio_base64 = base64.b64encode(response.content).decode("utf-8")

                    # Estimate duration (rough: 150 chars ~ 10 seconds at normal speed)
                    duration = (len(text) / 15) * (1.0 / speed)

                    return {
                        "audio_data": audio_base64,
                        "format": "mp3",
                        "duration_seconds": round(duration, 2),
                        "voice": voice,
                        "language": language
                    }
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code}")
                    return {
                        "audio_data": "",
                        "error": f"API error: {response.status_code}",
                        "format": "mp3"
                    }

        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {str(e)}")
            return {
                "audio_data": "",
                "error": str(e),
                "format": "mp3"
            }

    def _get_voice_id(self, voice: str) -> str:
        """
        Resolve voice name to voice ID.

        In production, this would fetch from ElevenLabs voices endpoint.
        """
        # Voice name to ID mapping (these are example IDs)
        voice_map = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Josh": "TxGEqnHWrfWFTfGW9XjX",
            "Dorothy": "ThT5KcBeYPX3keUQqHPh",
            "Charlotte": "Xb7YbHqAKbFkMDLpXb7Y",
            "default": "21m00Tcm4TlvDq8ikWAM"
        }

        return voice_map.get(voice, voice_map["default"])

    def get_available_voices(self) -> list:
        """
        Get list of available voices.
        """
        return [
            {"name": "Rachel", "description": "Clear, professional female"},
            {"name": "Josh", "description": "Professional male"},
            {"name": "Dorothy", "description": "Warm, friendly female"},
            {"name": "Charlotte", "description": "Multi-language support"}
        ]


# Singleton instance for application use
_tts_instance: Optional[ElevenLabsTTS] = None


def get_tts_handler() -> ElevenLabsTTS:
    """
    Get or create ElevenLabs TTS singleton.
    """
    global _tts_instance

    if _tts_instance is None:
        try:
            _tts_instance = ElevenLabsTTS()
        except ValueError as e:
            logger.error(f"Failed to initialize ElevenLabs TTS: {e}")
            raise

    return _tts_instance