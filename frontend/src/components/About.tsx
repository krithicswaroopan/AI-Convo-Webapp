import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const About: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          About
        </Typography>
        <Typography variant="body1">
          Real-time Conversational AI Assistant
        </Typography>
        <Typography variant="body2" sx={{ mt: 2 }}>
          This is a voice-enabled AI assistant that uses WebRTC, ASR, and TTS technologies.
        </Typography>
      </Paper>
    </Box>
  );
};

export default About; 