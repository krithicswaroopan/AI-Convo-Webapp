"""Speech-to-Text service using OpenAI Whisper."""

import logging
import asyncio
from typing import Optional
import httpx
from app.config import settings
from app.models.audio import TranscriptionRequest, TranscriptionResponse
from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)


class ASRService:
    """Speech-to-Text service using OpenAI Whisper."""
    
    def __init__(self):
        """Initialize the ASR service."""
        self.api_key = settings.openai_api_key  # Make sure to add this to config.py
        self.base_url = "https://api.openai.com/v1"
        self.model = settings.whisper_model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def transcribe_audio(
        self, 
        request: TranscriptionRequest,
        is_raw_pcm: bool = True,
        sample_rate: Optional[int] = None
    ) -> TranscriptionResponse:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            request: TranscriptionRequest containing audio data and parameters
            is_raw_pcm: Whether the audio data is raw PCM that needs WAV conversion
            
        Returns:
            TranscriptionResponse with transcribed text and metadata
        """
        try:
            logger.info(f"Starting transcription with model: {request.model or self.model}")
            
            # Convert raw PCM to WAV format if needed
            audio_data = request.audio_data
            if is_raw_pcm:
                try:
                    audio_data = audio_service.convert_pcm_to_wav(
                        request.audio_data,
                        sample_rate=sample_rate
                    )
                    logger.debug("Converted PCM audio to WAV format")
                except Exception as e:
                    logger.error(f"Failed to convert PCM to WAV: {str(e)}")
                    return TranscriptionResponse(
                        success=False,
                        text="",
                        language=None,
                        confidence=None,
                        duration_ms=None,
                        error=f"Audio format conversion failed: {str(e)}"
                    )
            
            # Prepare the request for OpenAI Whisper API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            
            files = {
                "file": ("audio.wav", audio_data, "audio/wav"),
                "model": (None, request.model or self.model),
                "language": (None, request.language) if request.language else None,
                "response_format": (None, "verbose_json"),
            }
            
            if request.prompt:
                files["prompt"] = (None, request.prompt)
            
            # Remove None values from files
            files = {k: v for k, v in files.items() if v is not None}
            
            # Make request to OpenAI Whisper API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=headers,
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return TranscriptionResponse(
                        success=True,
                        text=result.get("text", ""),
                        language=result.get("language"),
                        confidence=result.get("confidence"),
                        duration_ms=result.get("duration"),
                        error=None
                    )
                else:
                    error_msg = f"Whisper API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return TranscriptionResponse(
                        success=False,
                        text="",
                        language=None,
                        confidence=None,
                        duration_ms=None,
                        error=error_msg
                    )
                    
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return TranscriptionResponse(
                success=False,
                text="",
                language=None,
                confidence=None,
                duration_ms=None,
                error=error_msg
            )
    
    async def transcribe_streaming(
        self, 
        audio_chunk: bytes,
        language: Optional[str] = None,
        sample_rate: Optional[int] = None
    ) -> Optional[str]:
        """
        Transcribe a streaming audio chunk.
        
        Args:
            audio_chunk: Raw PCM audio data chunk
            language: Language code for transcription
            sample_rate: Audio sample rate
            
        Returns:
            Transcribed text or None if no speech detected
        """
        try:
            # For streaming, we'll use a smaller model and faster processing
            request = TranscriptionRequest(
                audio_data=audio_chunk,
                language=language or "en",
                model="whisper-1",  # Use base model for speed
                prompt=None
            )
            
            response = await self.transcribe_audio(request, is_raw_pcm=True, sample_rate=sample_rate)
            
            if response.success and response.text.strip():
                return response.text.strip()
            return None
            
        except Exception as e:
            logger.error(f"Streaming transcription failed: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global ASR service instance
asr_service = ASRService() 