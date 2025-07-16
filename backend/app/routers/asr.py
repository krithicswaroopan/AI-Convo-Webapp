"""ASR (Speech-to-Text) API router."""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.services.asr_service import asr_service
from app.models.audio import TranscriptionRequest, TranscriptionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asr", tags=["Speech-to-Text"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(default="en", description="Language code for transcription"),
    model: str = Form(default="whisper-1", description="Whisper model to use"),
    prompt: str = Form(default=None, description="Optional prompt for context")
):
    """
    Transcribe audio file to text using OpenAI Whisper.
    
    Args:
        file: Audio file (WAV, MP3, M4A, etc.)
        language: Language code (e.g., 'en', 'es', 'fr')
        model: Whisper model to use
        prompt: Optional context prompt
        
    Returns:
        TranscriptionResponse with transcribed text and metadata
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an audio file."
            )
        
        # Read audio data
        audio_data = await file.read()
        
        if not audio_data:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file provided."
            )
        
        logger.info(f"Transcribing audio file: {file.filename}, size: {len(audio_data)} bytes")
        
        # Create transcription request
        request = TranscriptionRequest(
            audio_data=audio_data,
            language=language,
            model=model,
            prompt=prompt
        )
        
        # Perform transcription (uploaded files are already in proper format)
        response = await asr_service.transcribe_audio(request, is_raw_pcm=False)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {response.error}"
            )
        
        logger.info(f"Transcription successful: {len(response.text)} characters")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during transcription"
        )


@router.post("/transcribe-streaming", response_model=TranscriptionResponse)
async def transcribe_streaming_audio(
    file: UploadFile = File(..., description="Audio file for streaming transcription"),
    language: str = Form(default="en", description="Language code")
):
    """
    Transcribe audio file optimized for streaming scenarios.
    
    Args:
        file: Audio file
        language: Language code
        
    Returns:
        TranscriptionResponse with transcribed text
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an audio file."
            )
        
        # Read audio data
        audio_data = await file.read()
        
        if not audio_data:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file provided."
            )
        
        logger.info(f"Streaming transcription for file: {file.filename}")
        
        # Use streaming transcription
        text = await asr_service.transcribe_streaming(audio_data, language)
        
        if text is None:
            raise HTTPException(
                status_code=500,
                detail="Streaming transcription failed"
            )
        
        return TranscriptionResponse(
            success=True,
            text=text,
            language=language,
            confidence=None,
            duration_ms=None,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during streaming transcription"
        )


@router.get("/health")
async def asr_health_check():
    """
    Health check for ASR service.
    
    Returns:
        Health status of the ASR service
    """
    try:
        # Basic health check - could be extended to test API connectivity
        return {
            "status": "healthy",
            "service": "asr",
            "model": asr_service.model,
            "available": True
        }
    except Exception as e:
        logger.error(f"ASR health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "asr",
            "error": str(e),
            "available": False
        }


@router.get("/debug/vad-status")
async def get_vad_status():
    """Get current VAD and noise floor status for debugging."""
    try:
        from app.services.audio_service import audio_service
        return {
            "status": "success",
            "vad_info": audio_service.get_noise_floor_info(),
            "timestamp": None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": None
        }