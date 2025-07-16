"""Text-to-speech data models."""

from typing import Optional
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request model for text-to-speech synthesis."""
    
    text: str = Field(..., description="Text to synthesize to speech")
    voice: Optional[str] = Field(default="en-US-Neural2-F", description="Voice to use")
    language: Optional[str] = Field(default="en-US", description="Language code")
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0, description="Speech rate")
    pitch: Optional[float] = Field(default=0.0, ge=-20.0, le=20.0, description="Pitch adjustment")
    volume: Optional[float] = Field(default=0.0, ge=-96.0, le=16.0, description="Volume adjustment")
    format: Optional[str] = Field(default="mp3", description="Audio format (mp3, wav, ogg)")


class TTSResponse(BaseModel):
    """Response model for text-to-speech synthesis."""
    
    success: bool = Field(..., description="Whether synthesis was successful")
    audio_data: Optional[bytes] = Field(None, description="Synthesized audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    duration_ms: Optional[float] = Field(None, description="Audio duration in milliseconds")
    word_count: Optional[int] = Field(None, description="Number of words in text")
    voice_used: Optional[str] = Field(None, description="Voice used for synthesis")
    error: Optional[str] = Field(None, description="Error message if synthesis failed") 