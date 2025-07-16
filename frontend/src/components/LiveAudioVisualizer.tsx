import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, keyframes } from '@mui/material';
import { Mic, MicOff, VolumeUp } from '@mui/icons-material';

interface LiveAudioVisualizerProps {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking?: boolean;
  hasVoiceActivity: boolean;
  currentTranscript: string;
  error: string | null;
}

const pulseAnimation = keyframes`
  0%, 100% { 
    transform: scale(1);
    opacity: 0.7;
  }
  50% { 
    transform: scale(1.1);
    opacity: 1;
  }
`;

const rippleAnimation = keyframes`
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
`;

const LiveAudioVisualizer: React.FC<LiveAudioVisualizerProps> = ({
  isListening,
  isProcessing,
  isSpeaking = false,
  hasVoiceActivity,
  currentTranscript,
  error
}) => {
  const [visualizerBars, setVisualizerBars] = useState<number[]>([]);
  
  useEffect(() => {
    if (isListening && hasVoiceActivity) {
      // Simulate audio levels for visualization
      const interval = setInterval(() => {
        const bars = Array.from({ length: 20 }, () => Math.random() * 100);
        setVisualizerBars(bars);
      }, 100);
      
      return () => clearInterval(interval);
    } else {
      setVisualizerBars(Array.from({ length: 20 }, () => 5));
    }
  }, [isListening, hasVoiceActivity]);
  
  const getStatusColor = () => {
    if (error) return 'error.main';
    if (isSpeaking) return 'secondary.main';
    if (isProcessing) return 'warning.main';
    if (hasVoiceActivity) return 'success.main';
    if (isListening) return 'primary.main';
    return 'grey.500';
  };
  
  const getStatusText = () => {
    if (error) return 'Error';
    if (isSpeaking) return 'Speaking...';
    if (isProcessing) return 'Processing...';
    if (hasVoiceActivity) return 'Voice Detected';
    if (isListening) return 'Listening...';
    return 'Inactive';
  };

  const getStatusIcon = () => {
    if (error) return <MicOff sx={{ color: 'white', fontSize: 20 }} />;
    if (isSpeaking) return <VolumeUp sx={{ color: 'white', fontSize: 20 }} />;
    return <Mic sx={{ color: 'white', fontSize: 20 }} />;
  };
  
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
      }}
    >
      <Paper
        elevation={6}
        sx={{
          p: 2,
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          minWidth: 300,
          textAlign: 'center',
        }}
      >
        {/* Status Indicator */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Ripple Effect */}
            {(hasVoiceActivity || isSpeaking) && (
              <Box
                sx={{
                  position: 'absolute',
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  border: '2px solid',
                  borderColor: getStatusColor(),
                  animation: `${rippleAnimation} 1s ease-out infinite`,
                }}
              />
            )}
            
            {/* Main Icon */}
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                backgroundColor: getStatusColor(),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                animation: (isListening || isSpeaking) ? `${pulseAnimation} 2s ease-in-out infinite` : 'none',
              }}
            >
              {getStatusIcon()}
            </Box>
          </Box>
          
          <Typography
            variant="body2"
            sx={{
              ml: 2,
              color: getStatusColor(),
              fontWeight: 600,
            }}
          >
            {getStatusText()}
          </Typography>
        </Box>
        
        {/* Audio Visualizer */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            height: 40,
            gap: 1,
            mb: 2,
          }}
        >
          {visualizerBars.map((height, index) => (
            <Box
              key={index}
              sx={{
                width: 3,
                height: `${Math.max(height, 5)}%`,
                backgroundColor: hasVoiceActivity ? 'success.main' : 'grey.600',
                borderRadius: 1,
                transition: 'height 0.1s ease-out',
                opacity: hasVoiceActivity ? 1 : 0.3,
              }}
            />
          ))}
        </Box>
        
        {/* Current Transcript */}
        {currentTranscript && (
          <Typography
            variant="body2"
            sx={{
              color: 'white',
              fontStyle: 'italic',
              maxWidth: 250,
              wordBreak: 'break-word',
              opacity: 0.8,
            }}
          >
            "{currentTranscript}"
          </Typography>
        )}
        
        {/* Error Message */}
        {error && (
          <Typography
            variant="caption"
            sx={{
              color: 'error.main',
              display: 'block',
              mt: 1,
            }}
          >
            {error}
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default LiveAudioVisualizer;