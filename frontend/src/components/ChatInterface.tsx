import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

import { useContinuousAudio } from '../hooks/useContinuousAudio.ts';
import { useTTS } from '../hooks/useTTS.ts';
import LiveAudioVisualizer from './LiveAudioVisualizer.tsx';
import ResponseDisplay from './ResponseDisplay.tsx';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audioUrl?: string;
  rating?: number;
}

interface VoiceSession {
  transcription: string;
  response: string;
  timestamp: Date;
  isComplete: boolean;
}

const ChatInterface: React.FC = () => {
  const [currentResponse, setCurrentResponse] = useState('');
  const [showResponse, setShowResponse] = useState(false);
  const [hasVoiceActivity, setHasVoiceActivity] = useState(false);
  const [isTTSComplete, setIsTTSComplete] = useState(false);
  const [voiceSessions, setVoiceSessions] = useState<VoiceSession[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Custom hooks
  const {
    isListening,
    isProcessing,
    currentTranscript,
    error: audioError,
    startListening,
    stopListening
  } = useContinuousAudio();
  
  const { synthesizeSpeech } = useTTS();

  // Auto-scroll to bottom when new sessions arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [voiceSessions]);

  // Handle voice activity detection
  useEffect(() => {
    setHasVoiceActivity(Boolean(currentTranscript));
  }, [currentTranscript]);

  // Handle WebSocket messages from continuous audio
  useEffect(() => {
    const handleWebSocketMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chat_response' && data.success) {
          setCurrentResponse(data.message);
          setShowResponse(true);
          
          // Create voice session
          const session: VoiceSession = {
            transcription: currentTranscript,
            response: data.message,
            timestamp: new Date(),
            isComplete: false
          };
          
          setVoiceSessions(prev => [...prev, session]);
        }
      } catch (error) {
        console.error('WebSocket message handling error:', error);
      }
    };

    // This would be handled by the continuous audio hook
    // Just showing the pattern here
  }, [currentTranscript]);

  // Handle TTS completion
  const handleTTSComplete = useCallback(async () => {
    try {
      if (currentResponse) {
        const audioData = await synthesizeSpeech(currentResponse);
        
        if (audioData) {
          const audioUrl = URL.createObjectURL(audioData);
          const audio = new Audio(audioUrl);
          
          audio.onended = () => {
            setIsTTSComplete(true);
            URL.revokeObjectURL(audioUrl);
          };
          
          await audio.play();
        }
      }
    } catch (error) {
      toast.error('Failed to synthesize speech');
      console.error('TTS error:', error);
    }
  }, [currentResponse, synthesizeSpeech]);

  // Handle response fade completion
  const handleResponseFade = useCallback(() => {
    setShowResponse(false);
    setCurrentResponse('');
    setIsTTSComplete(false);
  }, []);

  // Handle errors
  useEffect(() => {
    if (audioError) {
      toast.error(audioError);
    }
  }, [audioError]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Live Audio Visualizer */}
      <LiveAudioVisualizer
        isListening={isListening}
        isProcessing={isProcessing}
        hasVoiceActivity={hasVoiceActivity}
        currentTranscript={currentTranscript}
        error={audioError}
      />

      {/* Main Content Area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          p: 3,
          background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
          minHeight: '100vh',
        }}
      >
        {/* Error Alert */}
        {audioError && (
          <Alert severity="error" sx={{ mb: 3, maxWidth: 500 }}>
            {audioError}
          </Alert>
        )}

        {/* Welcome Message */}
        {!currentResponse && !isProcessing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Typography
              variant="h3"
              sx={{
                textAlign: 'center',
                mb: 2,
                fontWeight: 300,
                background: 'linear-gradient(45deg, #667eea, #764ba2)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Voice AI Assistant
            </Typography>
            <Typography
              variant="h6"
              sx={{
                textAlign: 'center',
                color: 'text.secondary',
                fontWeight: 300,
                maxWidth: 600,
              }}
            >
              {isListening ? 'Listening... Speak naturally and I\'ll respond' : 'Initializing voice recognition...'}
            </Typography>
          </motion.div>
        )}

        {/* Response Display */}
        <ResponseDisplay
          response={currentResponse}
          isVisible={showResponse}
          onTTSComplete={handleTTSComplete}
        />

        {/* Voice Sessions History (Hidden but tracked) */}
        <Box sx={{ display: 'none' }}>
          {voiceSessions.map((session, index) => (
            <Box key={index}>
              <Typography variant="caption">
                {session.transcription} → {session.response}
              </Typography>
            </Box>
          ))}
        </Box>

        <div ref={messagesEndRef} />
      </Box>
    </Box>
  );
};

export default ChatInterface;