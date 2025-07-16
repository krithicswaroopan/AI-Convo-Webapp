import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

interface ResponseDisplayProps {
  response: string;
  isVisible: boolean;
  onTTSComplete: () => void;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ 
  response, 
  isVisible, 
  onTTSComplete 
}) => {
  const [displayText, setDisplayText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const [fadeTimeout, setFadeTimeout] = useState<number | null>(null);
  
  const TYPING_SPEED = 50; // ms per character
  const FADE_DELAY = 20000; // 20 seconds
  
  const typeText = useCallback(async (text: string) => {
    setIsTyping(true);
    setDisplayText('');
    
    for (let i = 0; i <= text.length; i++) {
      setDisplayText(text.substring(0, i));
      await new Promise(resolve => setTimeout(resolve, TYPING_SPEED));
    }
    
    setIsTyping(false);
    onTTSComplete(); // Notify that typing is complete for TTS
  }, [onTTSComplete]);
  
  const startFadeTimer = useCallback(() => {
    if (fadeTimeout) {
      window.clearTimeout(fadeTimeout);
    }
    
    const timeout = window.setTimeout(() => {
      setShowResponse(false);
      setDisplayText('');
    }, FADE_DELAY);
    
    setFadeTimeout(timeout);
  }, [fadeTimeout]);
  
  useEffect(() => {
    if (response && isVisible) {
      setShowResponse(true);
      typeText(response);
    }
  }, [response, isVisible, typeText]);
  
  useEffect(() => {
    if (!isTyping && displayText) {
      startFadeTimer();
    }
    
    return () => {
      if (fadeTimeout) {
        window.clearTimeout(fadeTimeout);
      }
    };
  }, [isTyping, displayText, startFadeTimer, fadeTimeout]);
  
  return (
    <AnimatePresence>
      {showResponse && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 3,
              mb: 3,
              maxWidth: '80%',
              mx: 'auto',
              background: 'rgba(26, 26, 26, 0.9)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 3,
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: 'white',
                fontWeight: 400,
                lineHeight: 1.6,
                textAlign: 'center',
                minHeight: '2rem',
              }}
            >
              {displayText}
              {isTyping && (
                <motion.span
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                  style={{ color: 'primary.main' }}
                >
                  |
                </motion.span>
              )}
            </Typography>
          </Paper>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ResponseDisplay;