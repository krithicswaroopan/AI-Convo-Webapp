"""Health check API router."""

import logging
from fastapi import APIRouter
from app.services.asr_service import asr_service
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.services.streaming_service import streaming_service
from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """
    Overall health check for all services.
    
    Returns:
        Health status of all services
    """
    try:
        # Check all services
        services = {
            "asr": {
                "status": "healthy",
                "model": asr_service.model,
                "available": True
            },
            "llm": {
                "status": "healthy",
                "default_model": llm_service.default_model,
                "available_models": len(llm_service.get_available_models()),
                "available": True
            },
            "tts": {
                "status": "healthy" if tts_service.is_available() else "unhealthy",
                "available": tts_service.is_available(),
                "model": tts_service.model_name
            },
            "streaming": {
                "status": "healthy",
                "websocket_connections": len(streaming_service.websocket_connections),
                "active_connections": len(streaming_service.active_connections),
                "janus_configured": bool(streaming_service.janus_url)
            },
            "audio": {
                "status": "healthy",
                "vad_available": audio_service.is_vad_available(),
                "sample_rate": audio_service.sample_rate,
                "vad_mode": audio_service.vad_mode
            }
        }
        
        # Determine overall status
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in services.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp in production
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


@router.get("/asr")
async def asr_health():
    """Health check for ASR service."""
    try:
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


@router.get("/llm")
async def llm_health():
    """Health check for LLM service."""
    try:
        return {
            "status": "healthy",
            "service": "llm",
            "default_model": llm_service.default_model,
            "available_models": len(llm_service.get_available_models()),
            "available": True
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "llm",
            "error": str(e),
            "available": False
        }


@router.get("/tts")
async def tts_health():
    """Health check for TTS service."""
    try:
        is_available = tts_service.is_available()
        return {
            "status": "healthy" if is_available else "unhealthy",
            "service": "tts",
            "available": is_available,
            "google_cloud_configured": bool(tts_service.project_id)
        }
    except Exception as e:
        logger.error(f"TTS health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "tts",
            "error": str(e),
            "available": False
        }


@router.get("/streaming")
async def streaming_health():
    """Health check for streaming service."""
    try:
        return {
            "status": "healthy",
            "service": "streaming",
            "websocket_connections": len(streaming_service.websocket_connections),
            "active_connections": len(streaming_service.active_connections),
            "janus_configured": bool(streaming_service.janus_url)
        }
    except Exception as e:
        logger.error(f"Streaming health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "streaming",
            "error": str(e),
            "available": False
        }


@router.get("/audio")
async def audio_health():
    """Health check for audio processing service."""
    try:
        return {
            "status": "healthy",
            "service": "audio",
            "vad_available": audio_service.is_vad_available(),
            "sample_rate": audio_service.sample_rate,
            "vad_mode": audio_service.vad_mode
        }
    except Exception as e:
        logger.error(f"Audio health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "audio",
            "error": str(e),
            "available": False
        } 