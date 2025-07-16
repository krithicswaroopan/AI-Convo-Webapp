"""Text-to-Speech service using Coqui TTS."""

import logging
import asyncio
import tempfile
import os
from typing import Optional
import subprocess
import io
from app.config import settings
from app.models.tts import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using Coqui TTS."""
    
    def __init__(self):
        """Initialize the TTS service."""
        self.model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        self.available_voices = [
            "ljspeech",  # Default LJSpeech voice
            "vctk/p225",  # VCTK voices
            "vctk/p226",
            "vctk/p227",
            "vctk/p228",
            "vctk/p229",
            "vctk/p230",
        ]
        self._tts_available = False
        self._check_coqui_installation()
    
    def _check_coqui_installation(self):
        """Check if Coqui TTS is installed and available."""
        try:
            # Try to import TTS
            from TTS.api import TTS  # type: ignore
            
            # Initialize TTS with the model (this will download if needed)
            self._tts = TTS(model_name=self.model_name)
            
            logger.info("Coqui TTS is available")
            self._tts_available = True
        except ImportError as e:
            logger.warning(f"Coqui TTS not installed. Error: {str(e)}")
            self._install_coqui_tts()
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {str(e)}")
            self._tts_available = False
    
    def _install_coqui_tts(self):
        """Install Coqui TTS if not available."""
        try:
            subprocess.check_call([
                "pip", "install", "TTS", "--quiet"
            ])
            from TTS.api import TTS  # type: ignore
            
            # Initialize TTS with the model (this will download if needed)
            self._tts = TTS(model_name=self.model_name)
            
            self._tts_available = True
            logger.info("Coqui TTS installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Coqui TTS: {str(e)}")
            self._tts_available = False
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize text to speech using Coqui TTS.
        
        Args:
            request: TTSRequest containing text and voice parameters
            
        Returns:
            TTSResponse with audio data and metadata
        """
        try:
            if not self.is_available():
                logger.error("TTS service is not available")
                return TTSResponse(
                    success=False,
                    audio_data=None,
                    audio_url=None,
                    duration_ms=None,
                    word_count=None,
                    voice_used=None,
                    error="Coqui TTS is not available"
                )
            
            logger.info(f"Synthesizing speech for text: {request.text[:50]}...")
            
            # Use the specified voice or default
            voice = request.voice if request.voice in self.available_voices else "ljspeech"
            speed = request.speed if request.speed is not None else 1.0
            
            # Run TTS synthesis in a separate process
            audio_data = await self._run_tts_synthesis(request.text, voice, speed)
            
            if audio_data:
                # Calculate word count
                word_count = len(request.text.split())
                
                # Estimate duration (rough calculation)
                duration_ms = (word_count * 600) / speed  # ~600ms per word at normal speed
                
                return TTSResponse(
                    success=True,
                    audio_data=audio_data,
                    audio_url=None,
                    duration_ms=duration_ms,
                    word_count=word_count,
                    voice_used=voice,
                    error=None
                )
            else:
                return TTSResponse(
                    success=False,
                    audio_data=None,
                    audio_url=None,
                    duration_ms=None,
                    word_count=None,
                    voice_used=None,
                    error="Failed to generate audio data"
                )
            
        except Exception as e:
            error_msg = f"TTS synthesis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return TTSResponse(
                success=False,
                audio_data=None,
                audio_url=None,
                duration_ms=None,
                word_count=None,
                voice_used=None,
                error=error_msg
            )
    
    async def _run_tts_synthesis(self, text: str, voice: str, speed: float) -> Optional[bytes]:
        """
        Run TTS synthesis in a separate process.
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed
            
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            # Create a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                output_path = temp_file.name
            
            # Synthesize speech
            wav = self._tts.tts(text=text)
            
            # Save to file
            import numpy as np
            import soundfile as sf
            sf.write(output_path, wav, self._tts.synthesizer.output_sample_rate)
            
            if os.path.exists(output_path):
                # Read the generated audio file
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up temporary file
                os.unlink(output_path)
             
                # Convert WAV to MP3 if needed
                if not output_path.endswith('.mp3'):
                    audio_data = await self._convert_wav_to_mp3(audio_data)
                
                return audio_data
            else:
                logger.error("TTS synthesis failed: output file not created")
                return None
                
        except Exception as e:
            logger.error(f"Error in TTS synthesis: {str(e)}", exc_info=True)
            return None
    
    async def _convert_wav_to_mp3(self, wav_data: bytes) -> bytes:
        """
        Convert WAV audio data to MP3 format.
        
        Args:
            wav_data: WAV audio data
            
        Returns:
            MP3 audio data
        """
        try:
            from pydub import AudioSegment
            import io
            
            # Load WAV data
            audio = AudioSegment.from_wav(io.BytesIO(wav_data))
            
            # Export as MP3
            output = io.BytesIO()
            audio.export(output, format="mp3")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting WAV to MP3: {str(e)}", exc_info=True)
            return wav_data
    
    async def synthesize_ssml(self, ssml_content: str, voice: str = "ljspeech") -> TTSResponse:
        """
        Synthesize SSML content to speech.
        
        Args:
            ssml_content: SSML markup content
            voice: Voice to use for synthesis
            
        Returns:
            TTSResponse with audio data and metadata
        """
        try:
            # Extract text from SSML (simple implementation)
            import re
            text = re.sub(r'<[^>]+>', '', ssml_content)
            
            return await self.synthesize_speech(TTSRequest(
                text=text,
                voice=voice,
                language="en-US"
            ))
            
        except Exception as e:
            error_msg = f"SSML TTS synthesis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return TTSResponse(
                success=False,
                error=error_msg
            )
    
    def get_available_voices(self, language_code: str = "en-US") -> list:
        """
        Get available voices for a language.
        
        Args:
            language_code: Language code to get voices for
            
        Returns:
            List of available voice names
        """
        return self.available_voices.copy()
    
    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self._tts_available


# Global TTS service instance
tts_service = TTSService() 