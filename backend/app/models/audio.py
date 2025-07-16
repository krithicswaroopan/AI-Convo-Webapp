"""Audio processing data models."""

from typing import Optional
from pydantic import BaseModel, Field


class AudioRequest(BaseModel):
    """Request model for audio processing."""
    
    audio_data: bytes = Field(..., description="Raw audio data in WAV/PCM format")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    format: str = Field(default="wav", description="Audio format (wav, pcm, mp3)")


class AudioResponse(BaseModel):
    """Response model for audio processing."""
    
    success: bool = Field(..., description="Whether the processing was successful")
    message: str = Field(..., description="Response message")
    audio_data: Optional[bytes] = Field(None, description="Processed audio data")
    duration_ms: Optional[float] = Field(None, description="Audio duration in milliseconds")


class TranscriptionRequest(BaseModel):
    """Request model for speech-to-text transcription."""
    
    audio_data: bytes = Field(..., description="Raw audio data")
    language: Optional[str] = Field(default="en", description="Language code for transcription")
    model: Optional[str] = Field(default="whisper-1", description="Whisper model to use")
    prompt: Optional[str] = Field(None, description="Optional prompt for context")


class TranscriptionResponse(BaseModel):
    """Response model for speech-to-text transcription."""
    
    success: bool = Field(..., description="Whether transcription was successful")
    text: str = Field(..., description="Transcribed text")
    language: Optional[str] = Field(None, description="Detected language")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    duration_ms: Optional[float] = Field(None, description="Audio duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if transcription failed") 