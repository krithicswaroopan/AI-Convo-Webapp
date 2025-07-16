import React from 'react';
import { Box, Paper, keyframes } from '@mui/material';

interface AudioVisualizerProps {
  isRecording: boolean;
  audioData?: number[];
}

const pulseAnimation = keyframes`
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
`;

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ 
  isRecording, 
  audioData = [] 
}) => {
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box
        sx={{
          height: 60,
          display: 'flex',
          alignItems: 'flex-end',
          gap: 1,
          backgroundColor: 'grey.100',
          p: 1,
          borderRadius: 1,
        }}
      >
        {isRecording ? (
          // Show animated bars when recording
          Array.from({ length: 20 }, (_, i) => (
            <Box
              key={i}
              sx={{
                width: 3,
                height: Math.random() * 40 + 10,
                backgroundColor: 'primary.main',
                borderRadius: 1,
                animation: `${pulseAnimation} 0.5s ease-in-out infinite`,
              }}
            />
          ))
        ) : (
          // Show static bars when not recording
          Array.from({ length: 20 }, (_, i) => (
            <Box
              key={i}
              sx={{
                width: 3,
                height: 5,
                backgroundColor: 'grey.400',
                borderRadius: 1,
              }}
            />
          ))
        )}
      </Box>
    </Paper>
  );
};

export default AudioVisualizer; 