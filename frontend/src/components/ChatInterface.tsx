import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

import { useAudioManager } from '../hooks/useAudioManager.ts';
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

  // Unified audio management hook
  const {
    audioState,
    isListening,
    isProcessing,
    isSpeaking,
    currentTranscript,
    currentResponse: audioResponse,
    error: audioError,
    startListening,
    stopListening,
    pauseListening,
    resumeListening
  } = useAudioManager();

  // Auto-scroll to bottom when new sessions arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [voiceSessions]);

  // Handle voice activity detection
  useEffect(() => {
    setHasVoiceActivity(Boolean(currentTranscript));
  }, [currentTranscript]);

  // Handle voice sessions from audio manager
  useEffect(() => {
    if (audioResponse && currentTranscript) {
      const session: VoiceSession = {
        transcription: currentTranscript,
        response: audioResponse,
        timestamp: new Date(),
        isComplete: isSpeaking || audioState === 'speaking'
      };
      
      setVoiceSessions(prev => {
        // Avoid duplicates by checking if this session already exists
        const lastSession = prev[prev.length - 1];
        if (lastSession && 
            lastSession.transcription === session.transcription && 
            lastSession.response === session.response) {
          return prev;
        }
        return [...prev, session];
      });
      
      setCurrentResponse(audioResponse);
      setShowResponse(true);
    }
  }, [audioResponse, currentTranscript, isSpeaking, audioState]);

  // Update TTS completion based on audio state
  useEffect(() => {
    if (audioState === 'listening' && isTTSComplete !== true) {
      setIsTTSComplete(true);
    } else if (audioState === 'speaking') {
      setIsTTSComplete(false);
    }
  }, [audioState, isTTSComplete]);

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
        isSpeaking={isSpeaking}
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
          response={currentResponse || audioResponse}
          isVisible={showResponse}
          onTTSComplete={() => {}} // TTS is now handled by audio manager
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