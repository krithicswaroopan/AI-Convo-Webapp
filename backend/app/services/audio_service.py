"""Audio processing service for VAD, noise suppression, and audio pipeline."""

import logging
import numpy as np
import webrtcvad
import io
import wave
from typing import Optional, Tuple, List
from app.config import settings

logger = logging.getLogger(__name__)


class AudioService:
    """Audio processing service for VAD and noise suppression."""
    
    def __init__(self):
        """Initialize the audio service."""
        self.sample_rate = settings.sample_rate
        self.chunk_duration_ms = settings.chunk_duration_ms
        self.vad_mode = settings.vad_mode
        
        # Initialize VAD
        try:
            self.vad = webrtcvad.Vad(self.vad_mode)
            logger.info(f"VAD initialized with mode {self.vad_mode}")
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {str(e)}")
            self.vad = None

    def convert_pcm_to_wav(
        self, 
        pcm_data: bytes, 
        sample_rate: Optional[int] = None,
        channels: int = 1,
        sample_width: int = 2
    ) -> bytes:
        """
        Convert raw PCM audio data to WAV format.
        
        Args:
            pcm_data: Raw PCM audio data
            sample_rate: Audio sample rate (defaults to configured rate)
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
            
        Returns:
            WAV-formatted audio data
        """
        try:
            sample_rate = sample_rate or self.sample_rate
            
            # Create an in-memory WAV file
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)
            
            # Get the WAV data
            wav_data = wav_buffer.getvalue()
            wav_buffer.close()
            
            logger.debug(f"Converted {len(pcm_data)} bytes PCM to {len(wav_data)} bytes WAV")
            return wav_data
            
        except Exception as e:
            logger.error(f"PCM to WAV conversion failed: {str(e)}")
            raise
    
    def process_audio_chunk(
        self, 
        audio_data: bytes,
        sample_rate: Optional[int] = None
    ) -> Tuple[bytes, bool]:
        """
        Process an audio chunk with VAD and noise suppression.
        
        Args:
            audio_data: Raw audio data
            sample_rate: Audio sample rate (defaults to configured rate)
            
        Returns:
            Tuple of (processed_audio, has_speech)
        """
        try:
            sample_rate = sample_rate or self.sample_rate
            
            # Check if VAD is available
            if not self.vad:
                return audio_data, True  # Assume speech if VAD not available
            
            # Calculate frame size for VAD
            frame_size = int(sample_rate * self.chunk_duration_ms / 1000)
            
            # Convert bytes to 16-bit PCM samples
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Process audio in frames
            has_speech = False
            processed_frames = []
            
            for i in range(0, len(audio_samples), frame_size):
                frame = audio_samples[i:i + frame_size]
                
                # Pad frame if necessary
                if len(frame) < frame_size:
                    frame = np.pad(frame, (0, frame_size - len(frame)), 'constant')
                
                # Convert to bytes for VAD
                frame_bytes = frame.tobytes()
                
                # Check for speech activity
                try:
                    if self.vad.is_speech(frame_bytes, sample_rate):
                        has_speech = True
                        processed_frames.append(frame)
                except Exception as e:
                    logger.warning(f"VAD processing error: {str(e)}")
                    processed_frames.append(frame)  # Include frame anyway
            
            if processed_frames:
                # Combine processed frames
                processed_audio = np.concatenate(processed_frames)
                return processed_audio.tobytes(), has_speech
            else:
                return audio_data, False
                
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return audio_data, True  # Return original audio on error
    
    def apply_noise_suppression(self, audio_data: bytes) -> bytes:
        """
        Apply basic noise suppression to audio data.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Noise-suppressed audio data
        """
        try:
            # Convert to numpy array
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Simple noise gate (remove very quiet parts)
            threshold = np.std(audio_samples) * 0.1
            audio_samples[np.abs(audio_samples) < threshold] = 0
            
            # Simple high-pass filter to remove low-frequency noise
            # This is a basic implementation - for production, use a proper filter
            if len(audio_samples) > 1:
                # Simple first-order high-pass filter
                alpha = 0.95
                filtered = np.zeros_like(audio_samples, dtype=np.float32)
                filtered[0] = audio_samples[0]
                
                for i in range(1, len(audio_samples)):
                    filtered[i] = alpha * (filtered[i-1] + audio_samples[i] - audio_samples[i-1])
                
                # Convert back to int16
                audio_samples = np.clip(filtered, -32768, 32767).astype(np.int16)
            
            return audio_samples.tobytes()
            
        except Exception as e:
            logger.error(f"Noise suppression failed: {str(e)}")
            return audio_data
    
    def normalize_audio(self, audio_data: bytes) -> bytes:
        """
        Normalize audio levels.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Normalized audio data
        """
        try:
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_samples.astype(np.float32) ** 2))
            
            if rms > 0:
                # Normalize to target RMS
                target_rms = 5000  # Adjustable target
                gain = target_rms / rms
                
                # Apply gain with clipping
                normalized = np.clip(audio_samples * gain, -32768, 32767)
                return normalized.astype(np.int16).tobytes()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Audio normalization failed: {str(e)}")
            return audio_data
    
    def detect_silence(self, audio_data: bytes, threshold_ms: int = 500) -> bool:
        """
        Detect if audio contains only silence.
        
        Args:
            audio_data: Raw audio data
            threshold_ms: Minimum silence duration in milliseconds
            
        Returns:
            True if audio is silent
        """
        try:
            if not self.vad:
                return False
            
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            frame_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
            
            silence_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_samples), frame_size):
                frame = audio_samples[i:i + frame_size]
                
                if len(frame) < frame_size:
                    frame = np.pad(frame, (0, frame_size - len(frame)), 'constant')
                
                frame_bytes = frame.tobytes()
                
                try:
                    if not self.vad.is_speech(frame_bytes, self.sample_rate):
                        silence_frames += 1
                    total_frames += 1
                except Exception:
                    total_frames += 1
            
            if total_frames == 0:
                return True
            
            silence_ratio = silence_frames / total_frames
            silence_duration_ms = (silence_ratio * len(audio_samples) / self.sample_rate) * 1000
            
            return silence_duration_ms >= threshold_ms
            
        except Exception as e:
            logger.error(f"Silence detection failed: {str(e)}")
            return False
    
    def get_audio_duration(self, audio_data: bytes) -> float:
        """
        Calculate audio duration in milliseconds.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Duration in milliseconds
        """
        try:
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            duration_seconds = len(audio_samples) / self.sample_rate
            return duration_seconds * 1000
        except Exception as e:
            logger.error(f"Duration calculation failed: {str(e)}")
            return 0.0
    
    def is_vad_available(self) -> bool:
        """Check if VAD is available."""
        return self.vad is not None


# Global audio service instance
audio_service = AudioService() 