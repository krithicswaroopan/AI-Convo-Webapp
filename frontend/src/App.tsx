import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import { Helmet } from 'react-helmet-async';

import Layout from './components/Layout.tsx';
import ChatInterface from './components/ChatInterface.tsx';
import Settings from './components/Settings.tsx';
import About from './components/About.tsx';
import NotFound from './components/NotFound.tsx';

const App: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>AI Assistant - Real-time Voice Conversations</title>
        <meta name="description" content="Real-time conversational AI assistant with voice capabilities" />
        <meta name="keywords" content="AI, assistant, voice, conversation, real-time, WebRTC" />
      </Helmet>
      
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          backgroundAttachment: 'fixed',
        }}
      >
        <Container maxWidth="xl" sx={{ py: 2 }}>
          <Layout>
            <Routes>
              <Route path="/" element={<ChatInterface />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/about" element={<About />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </Container>
      </Box>
    </>
  );
};

export default App; 