import { useState, useCallback, useRef } from 'react';

interface UseTTSReturn {
  isPlaying: boolean;
  isSynthesizing: boolean;
  playAudio: (audioBlob: Blob) => Promise<void>;
  stopAudio: () => void;
  synthesizeSpeech: (text: string) => Promise<Blob | null>;
}

export const useTTS = (): UseTTSReturn => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playAudio = useCallback(async (audioBlob: Blob) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  const synthesizeSpeech = useCallback(async (text: string): Promise<Blob | null> => {
    try {
      setIsSynthesizing(true);
      const response = await fetch('/api/v1/tts/synthesize-audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          voice: 'en-US-Neural2-F',
          language: 'en-US',
        }),
      });

      if (!response.ok) {
        throw new Error(`TTS synthesis failed: ${response.status} ${response.statusText}`);
      }

      const audioBlob = await response.blob();
      return audioBlob;
    } catch (error) {
      console.error('TTS synthesis error:', error);
      return null;
    } finally {
      setIsSynthesizing(false);
    }
  }, []);

  return {
    isPlaying,
    isSynthesizing,
    playAudio,
    stopAudio,
    synthesizeSpeech,
  };
}; 