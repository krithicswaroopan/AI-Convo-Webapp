"""TTS (Text-to-Speech) API router."""

import logging
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from app.services.tts_service import tts_service
from app.models.tts import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize text to speech using Coqui TTS.
    
    Args:
        request: TTSRequest containing text and voice parameters
        
    Returns:
        TTSResponse with audio data and metadata
    """
    try:
        logger.info(f"Synthesizing speech for text: {request.text[:50]}...")
        
        # Check if TTS service is available
        if not tts_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service is not available. Please check Coqui TTS installation."
            )
        
        # Synthesize speech
        response = await tts_service.synthesize_speech(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"TTS synthesis failed: {response.error}"
            )
        
        logger.info(f"TTS synthesis successful: {response.word_count} words, {response.duration_ms:.0f}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS synthesis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during TTS synthesis"
        )


@router.post("/synthesize-audio")
async def synthesize_speech_audio(request: TTSRequest):
    """
    Synthesize text to speech and return audio file directly.
    
    Args:
        request: TTSRequest containing text and voice parameters
        
    Returns:
        MP3 audio file
    """
    try:
        logger.info(f"Synthesizing audio for text: {request.text[:50]}...")
        
        # Check if TTS service is available
        if not tts_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service is not available. Please check Google Cloud credentials."
            )
        
        # Synthesize speech
        response = await tts_service.synthesize_speech(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"TTS synthesis failed: {response.error}"
            )
        
        # Return audio file
        return Response(
            content=response.audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Content-Length": str(len(response.audio_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS audio synthesis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during TTS synthesis"
        )


@router.post("/synthesize-streaming")
async def synthesize_speech_streaming(request: TTSRequest):
    """
    Synthesize text to speech and return as streaming audio.
    
    Args:
        request: TTSRequest containing text and voice parameters
        
    Returns:
        Streaming MP3 audio
    """
    try:
        logger.info(f"Streaming TTS synthesis for text: {request.text[:50]}...")
        
        # Check if TTS service is available
        if not tts_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service is not available. Please check Google Cloud credentials."
            )
        
        # Synthesize speech
        response = await tts_service.synthesize_speech(request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"TTS synthesis failed: {response.error}"
            )
        
        # Return streaming audio
        return StreamingResponse(
            iter([response.audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(len(response.audio_data)),
                "Accept-Ranges": "bytes"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS streaming synthesis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during TTS synthesis"
        )


@router.post("/synthesize-ssml")
async def synthesize_ssml(ssml_content: str, voice: str = "en-US-Neural2-F"):
    """
    Synthesize SSML content to speech.
    
    Args:
        ssml_content: SSML markup content
        voice: Voice to use for synthesis
        
    Returns:
        TTSResponse with audio data
    """
    try:
        logger.info("Synthesizing SSML content")
        
        # Check if TTS service is available
        if not tts_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS service is not available. Please check Google Cloud credentials."
            )
        
        # Synthesize SSML
        response = await tts_service.synthesize_ssml(ssml_content, voice)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"SSML TTS synthesis failed: {response.error}"
            )
        
        logger.info("SSML TTS synthesis successful")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSML TTS synthesis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during SSML TTS synthesis"
        )


@router.get("/voices")
async def get_available_voices(language_code: str = "en-US"):
    """
    Get available voices for a language.
    
    Args:
        language_code: Language code to get voices for
        
    Returns:
        List of available voice names
    """
    try:
        voices = tts_service.get_available_voices(language_code)
        return {
            "language_code": language_code,
            "voices": voices,
            "total_voices": len(voices)
        }
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available voices"
        )


@router.get("/health")
async def tts_health_check():
    """
    Health check for TTS service.
    
    Returns:
        Health status of the TTS service
    """
    try:
        is_available = tts_service.is_available()
        return {
            "status": "healthy" if is_available else "unhealthy",
            "service": "tts",
            "available": is_available,
            "model": tts_service.model_name
        }
    except Exception as e:
        logger.error(f"TTS health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "tts",
            "error": str(e),
            "available": False
        } 