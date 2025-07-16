import { useState, useRef, useCallback, useEffect } from 'react';

export type AudioState = 'idle' | 'listening' | 'processing' | 'speaking';

interface UseAudioManagerReturn {
  audioState: AudioState;
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  currentTranscript: string;
  currentResponse: string;
  error: string | null;
  startListening: () => Promise<void>;
  stopListening: () => void;
  pauseListening: () => void;
  resumeListening: () => void;
}

export const useAudioManager = (): UseAudioManagerReturn => {
  const [audioState, setAudioState] = useState<AudioState>('idle');
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [currentResponse, setCurrentResponse] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const connectionIdRef = useRef<string | null>(null);
  const isConnectedRef = useRef<boolean>(false);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const isPausedRef = useRef<boolean>(false);
  
  // Add refs for sequencing and debouncing
  const isProcessingSequenceRef = useRef<boolean>(false);
  const lastTranscriptRef = useRef<string>('');
  const lastResponseRef = useRef<string>('');
  const debounceTimeoutRef = useRef<number | null>(null);
  
  const SAMPLE_RATE = 16000;

  // Derived states
  const isListening = audioState === 'listening';
  const isProcessing = audioState === 'processing';
  const isSpeaking = audioState === 'speaking';

  const setAudioStateWithLog = useCallback((newState: AudioState) => {
    console.log(`Audio state transition: ${audioState} → ${newState}`);
    setAudioState(newState);
  }, [audioState]);
  
  // Debounced state setter to prevent rapid state changes
  const setAudioStateDebounced = useCallback((newState: AudioState, delay: number = 100) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    
    debounceTimeoutRef.current = window.setTimeout(() => {
      setAudioStateWithLog(newState);
      debounceTimeoutRef.current = null;
    }, delay);
  }, [setAudioStateWithLog]);

  const playTTSAudio = useCallback(async (audioDataHex: string) => {
    try {
      // Convert hex string to binary
      const audioBytes = new Uint8Array(
        audioDataHex.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []
      );
      
      // Create audio blob and play
      const audioBlob = new Blob([audioBytes], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Stop any existing audio
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
      
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;
      
      audio.onended = () => {
        console.log('TTS playback finished, resuming listening');
        URL.revokeObjectURL(audioUrl);
        audioPlayerRef.current = null;
        
        // Reset processing sequence
        isProcessingSequenceRef.current = false;
        
        // Resume listening after TTS finishes (if not manually paused)
        if (!isPausedRef.current) {
          setAudioStateDebounced('listening');
        }
      };
      
      audio.onerror = (err) => {
        console.error('Audio playback error:', err);
        URL.revokeObjectURL(audioUrl);
        audioPlayerRef.current = null;
        
        // Reset processing sequence
        isProcessingSequenceRef.current = false;
        
        // Resume listening on error (if not manually paused)
        if (!isPausedRef.current) {
          setAudioStateDebounced('listening');
        }
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error playing TTS audio:', error);
      
      // Reset processing sequence
      isProcessingSequenceRef.current = false;
      
      // Resume listening on error (if not manually paused)
      if (!isPausedRef.current) {
        setAudioStateDebounced('listening');
      }
    }
  }, [setAudioStateDebounced]);

  const initializeWebSocket = useCallback(async () => {
    if (websocketRef.current && isConnectedRef.current) {
      return;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    console.log('Initializing WebSocket connection to ws://localhost:8000/api/v1/streaming/ws...');
    
    // Add a small delay to prevent rapid reconnection attempts
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      const ws = new WebSocket('ws://localhost:8000/api/v1/streaming/ws');
      
      ws.onopen = () => {
        console.log('WebSocket connected for audio management');
        isConnectedRef.current = true;
        setError(null);
      };
    
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connection_established') {
            console.log('Connection established with ID:', data.connection_id);
            connectionIdRef.current = data.connection_id;
          } 
          else if (data.type === 'transcription_response') {
            if (data.success && data.text && data.text !== lastTranscriptRef.current) {
              // Prevent processing duplicate transcriptions
              if (isProcessingSequenceRef.current) {
                console.log('Skipping transcription - already processing sequence');
                return;
              }
              
              console.log('Transcription received:', data.text);
              lastTranscriptRef.current = data.text;
              setCurrentTranscript(data.text);
              setAudioStateWithLog('processing');
              
              // Mark sequence as processing
              isProcessingSequenceRef.current = true;
              
              // Send chat request immediately after transcription
              if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                  type: 'chat_request',
                  message: data.text
                }));
              }
            } else {
              // No text transcribed, resume listening
              if (!isPausedRef.current && !isProcessingSequenceRef.current) {
                setAudioStateDebounced('listening');
              }
            }
          } 
          else if (data.type === 'chat_response') {
            if (data.success && data.message && data.message !== lastResponseRef.current) {
              console.log('Chat response received:', data.message);
              lastResponseRef.current = data.message;
              setCurrentResponse(data.message);
              
              // Request TTS for the response
              if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                  type: 'tts_request',
                  text: data.message
                }));
              }
            } else {
              // Chat failed, resume listening
              isProcessingSequenceRef.current = false;
              if (!isPausedRef.current) {
                setAudioStateDebounced('listening');
              }
            }
          } 
          else if (data.type === 'tts_response') {
            if (data.success && data.audio_data) {
              console.log('TTS audio received, starting playback');
              setAudioStateWithLog('speaking');
              playTTSAudio(data.audio_data);
            } else {
              // TTS failed, resume listening
              console.error('TTS failed:', data.error);
              isProcessingSequenceRef.current = false;
              if (!isPausedRef.current) {
                setAudioStateDebounced('listening');
              }
            }
          }
          else if (data.type === 'error') {
            console.error('WebSocket error from server:', data.message);
            setError(data.message);
            isProcessingSequenceRef.current = false;
          }
        } catch (err) {
          console.error('WebSocket message error:', err);
          isProcessingSequenceRef.current = false;
        }
      };
    
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        isConnectedRef.current = false;
        setError('WebSocket connection error');
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
        isConnectedRef.current = false;
        websocketRef.current = null;
        
        if (event.code === 1012) {
          setError('Service restarting...');
        } else if (event.code === 1006) {
          setError('Connection failed - check if backend is running');
        } else if (event.code !== 1000) {
          setError('Connection lost');
        }
      };
      
      websocketRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setError('Failed to create WebSocket connection');
    }
  }, [setAudioStateDebounced, setAudioStateWithLog, playTTSAudio]);

  const startListening = useCallback(async () => {
    try {
      setError(null);
      isPausedRef.current = false;
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: SAMPLE_RATE,
          sampleSize: 16,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      streamRef.current = stream;
      
      // Initialize audio context for PCM extraction
      const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioContextRef.current = audioContext;
      
      // Resume audio context if suspended (required by Chrome)
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }
      
      console.log('Audio context state:', audioContext.state);
      
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      
      processor.onaudioprocess = (event) => {
        // Use ref instead of state to avoid closure issues
        if (!isPausedRef.current && websocketRef.current?.readyState === WebSocket.OPEN) {
          const inputBuffer = event.inputBuffer;
          const inputData = inputBuffer.getChannelData(0);
          
          console.log(`Processing audio: ${inputData.length} samples`);
          
          // Convert float32 to int16 PCM
          const int16Array = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const sample = Math.max(-1, Math.min(1, inputData[i]));
            int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
          }
          
          // Send PCM data
          try {
            websocketRef.current.send(JSON.stringify({
              type: 'audio_chunk',
              audio_data: Array.from(new Uint8Array(int16Array.buffer))
            }));
            console.log(`Sent audio chunk: ${int16Array.buffer.byteLength} bytes`);
          } catch (error) {
            console.error('Error sending audio chunk:', error);
          }
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      // Initialize WebSocket
      await initializeWebSocket();
      
      // Start audio processing
      setAudioStateWithLog('listening');
      
    } catch (err) {
      console.error('Error starting audio manager:', err);
      setError('Failed to start audio system');
    }
  }, [initializeWebSocket, setAudioStateWithLog]);
  
  const stopListening = useCallback(() => {
    isPausedRef.current = true;
    
    // Reset processing sequence
    isProcessingSequenceRef.current = false;
    
    // Clear debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'User stopped listening');
      websocketRef.current = null;
    }
    
    isConnectedRef.current = false;
    connectionIdRef.current = null;
    
    setAudioStateWithLog('idle');
    setCurrentTranscript('');
    setCurrentResponse('');
    setError(null);
    
    // Reset tracking refs
    lastTranscriptRef.current = '';
    lastResponseRef.current = '';
  }, [setAudioStateWithLog]);

  const pauseListening = useCallback(() => {
    isPausedRef.current = true;
    setAudioStateWithLog('idle');
  }, [setAudioStateWithLog]);

  const resumeListening = useCallback(() => {
    if (streamRef.current && audioContextRef.current) {
      isPausedRef.current = false;
      setAudioStateWithLog('listening');
    }
  }, [setAudioStateWithLog]);

  // Auto-start listening when component mounts
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await startListening();
      } catch (error) {
        console.error('Failed to initialize audio:', error);
        setError('Failed to initialize audio system');
      }
    };
    
    initializeApp();
    
    return () => {
      stopListening();
    };
  }, [startListening, stopListening]);
  
  return {
    audioState,
    isListening,
    isProcessing,
    isSpeaking,
    currentTranscript,
    currentResponse,
    error,
    startListening,
    stopListening,
    pauseListening,
    resumeListening
  };
};