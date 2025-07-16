"""API routers for the AI Assistant application."""

from .asr import router as asr_router
from .chat import router as chat_router
from .tts import router as tts_router
from .streaming import router as streaming_router
from .health import router as health_router

__all__ = [
    "asr_router",
    "chat_router", 
    "tts_router",
    "streaming_router",
    "health_router",
] 