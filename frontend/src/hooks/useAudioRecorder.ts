/// <reference types="node" />
import { useState, useRef, useCallback } from 'react';

interface UseAudioRecorderReturn {
  isRecording: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  audioBlob: Blob | null;
}

export const useAudioRecorder = (): UseAudioRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const stopPromiseResolveRef = useRef<((blob: Blob) => void) | null>(null);

  const startRecording = useCallback(async () => {
    try {
      // Request audio with specific constraints for better compatibility
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1, // Mono
          sampleRate: 16000, // 16kHz
          sampleSize: 16, // 16-bit
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      // Create MediaRecorder with WAV MIME type
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm', // We'll convert to WAV later
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Convert to WAV format
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        
        // Convert to WAV using Web Audio API
        const audioContext = new AudioContext({ sampleRate: 16000 });
        const arrayBuffer = await blob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Create WAV file
        const wavBlob = await convertToWav(audioBuffer);
        setAudioBlob(wavBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        if (stopPromiseResolveRef.current) {
          stopPromiseResolveRef.current(wavBlob);
          stopPromiseResolveRef.current = null;
        }
      };

      // Request data every 1 second
      mediaRecorder.start(1000);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      throw error;
    }
  }, [convertToWav]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    if (mediaRecorderRef.current && isRecording) {
      return new Promise((resolve) => {
        stopPromiseResolveRef.current = resolve;
        mediaRecorderRef.current!.stop();
        setIsRecording(false);
      });
    }
    return null;
  }, [isRecording]);

  // Helper function to convert AudioBuffer to WAV
  const convertToWav = async (audioBuffer: AudioBuffer): Promise<Blob> => {
    const numOfChannels = 1; // Mono
    const sampleRate = audioBuffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
    
    const length = audioBuffer.length * numOfChannels * 2; // 2 bytes per sample
    const buffer = new ArrayBuffer(44 + length); // 44 bytes for WAV header
    const view = new DataView(buffer);
    
    // Write WAV header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, format, true);
    view.setUint16(22, numOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numOfChannels * 2, true);
    view.setUint16(32, numOfChannels * 2, true);
    view.setUint16(34, bitDepth, true);
    writeString(view, 36, 'data');
    view.setUint32(40, length, true);
    
    // Write audio data
    const data = audioBuffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < data.length; i++) {
      const sample = Math.max(-1, Math.min(1, data[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  };

  // Helper function to write strings to DataView
  const writeString = (view: DataView, offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  return {
    isRecording,
    startRecording,
    stopRecording,
    audioBlob,
  };
}; 