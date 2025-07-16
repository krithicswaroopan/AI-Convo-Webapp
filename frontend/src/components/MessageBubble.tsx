import React, { memo } from 'react';
import { Box, Typography, Paper, IconButton, Rating } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon } from '@mui/icons-material';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audioUrl?: string;
  rating?: number;
}

interface MessageBubbleProps {
  message: Message;
  onRate?: (messageId: string, rating: number) => void;
  onPlayAudio?: () => void;
  isPlaying?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onRate, onPlayAudio, isPlaying }) => {
  const isUser = message.role === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Paper
        sx={{
          p: 2,
          maxWidth: '70%',
          backgroundColor: isUser ? 'primary.main' : 'grey.100',
          color: isUser ? 'white' : 'text.primary',
        }}
      >
        <Typography variant="body1">{message.content}</Typography>
        
        {/* Audio playback controls */}
        {message.audioUrl && onPlayAudio && (
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              size="small"
              onClick={onPlayAudio}
              sx={{ color: isUser ? 'white' : 'primary.main' }}
            >
              {isPlaying ? <PauseIcon /> : <PlayIcon />}
            </IconButton>
          </Box>
        )}

        {/* Rating for assistant messages */}
        {!isUser && onRate && (
          <Box sx={{ mt: 1 }}>
            <Rating
              size="small"
              value={message.rating || 0}
              onChange={(_, value) => value && onRate(message.id, value)}
            />
          </Box>
        )}

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            opacity: 0.7,
          }}
        >
          {message.timestamp.toLocaleTimeString()}
        </Typography>
      </Paper>
    </Box>
  );
};

export default memo(MessageBubble); 