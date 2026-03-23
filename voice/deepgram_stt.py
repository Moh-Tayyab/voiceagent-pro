"""
Deepgram STT Handler - Real-time speech-to-text transcription

Handles streaming audio transcription using Deepgram API.
"""

import os
import logging
import asyncio
from typing import Optional, AsyncGenerator

from deepgram import DeepgramClient, PrerecordedOptions, ListenRESTSource

logger = logging.getLogger(__name__)


class DeepgramSTT:
    """
    Deepgram Speech-to-Text handler.

    Supports both real-time streaming and prerecorded transcription.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Deepgram client.

        Args:
            api_key: Deepgram API key (defaults to DEEPGRAM_API_KEY env)
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")

        if not self.api_key:
            logger.error("Deepgram API key not configured")
            raise ValueError("Deepgram API key required")

        self.client = DeepgramClient(api_key=self.api_key)

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        model: str = "nova-2",
        smart_format: bool = True
    ) -> dict:
        """
        Transcribe audio data using Deepgram prerecorded API.

        Args:
            audio_data: Raw audio bytes
            language: Language code (en, ur, es, etc.)
            model: Deepgram model to use
            smart_format: Enable smart formatting

        Returns:
            Dict with transcript, confidence, and metadata
        """
        try:
            logger.debug(f"Transcribing audio: {len(audio_data)} bytes")

            # Configure options
            options = PrerecordedOptions(
                model=model,
                language=language,
                smart_format=smart_format,
                punctuate=True,
                utterances=True,
                detect_language=False  # We provide language explicitly
            )

            # Create source
            source = ListenRESTSource(buffer=audio_data)

            # Transcribe
            response = self.client.listen.rest.v("1").transcribe_file(source, options)

            # Extract results
            if response.results.channels and response.results.channels[0].alternatives:
                transcript = response.results.channels[0].alternatives[0].transcript
                confidence = response.results.channels[0].alternatives[0].confidence

                return {
                    "transcript": transcript,
                    "confidence": confidence,
                    "language": language,
                    "duration": response.results.duration,
                    "words": response.results.channels[0].alternatives[0].words
                }

            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "duration": 0.0,
                "error": "No transcription result"
            }

        except Exception as e:
            logger.error(f"Deepgram transcription error: {str(e)}")
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "error": str(e)
            }

    async def transcribe_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
        language: str = "en"
    ) -> AsyncGenerator[dict, None]:
        """
        Transcribe streaming audio in real-time.

        This is a placeholder for WebSocket streaming implementation.
        In production, use Deepgram's live streaming API.

        Args:
            audio_chunks: Async generator yielding audio chunks
            language: Language code

        Yields:
            Transcription results for each chunk
        """
        try:
            # In production, this would use:
            # self.client.listen.asyncrestart.v("1").stream

            async for chunk in audio_chunks:
                result = await self.transcribe_audio(chunk, language)
                yield result

        except Exception as e:
            logger.error(f"Stream transcription error: {str(e)}")
            yield {
                "transcript": "",
                "error": str(e)
            }

    def detect_language(self, transcript: str) -> str:
        """
        Detect language from transcript.

        Simple heuristic based on common words.
        In production, use langdetect or similar library.
        """
        urdu_markers = ["kya", "kaise", "kab", "kahan", "kyun", "mein", "hum", "ap", "hai"]
        english_markers = ["what", "how", "when", "where", "why", "i", "you", "is", "are"]

        transcript_lower = transcript.lower()

        ur_count = sum(1 for marker in urdu_markers if marker in transcript_lower)
        en_count = sum(1 for marker in english_markers if marker in transcript_lower)

        return "ur" if ur_count > en_count else "en"


# Singleton instance for application use
_stt_instance: Optional[DeepgramSTT] = None


def get_stt_handler() -> DeepgramSTT:
    """
    Get or create Deepgram STT singleton.
    """
    global _stt_instance

    if _stt_instance is None:
        try:
            _stt_instance = DeepgramSTT()
        except ValueError as e:
            logger.error(f"Failed to initialize Deepgram STT: {e}")
            raise

    return _stt_instance