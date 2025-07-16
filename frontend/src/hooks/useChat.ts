import { useState, useCallback } from 'react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatResponse {
  success: boolean;
  message: string;
  error?: string;
}

interface UseChatReturn {
  messages: Message[];
  addMessage: (text: string, sender: 'user' | 'assistant') => void;
  clearMessages: () => void;
  generateResponse: (text: string) => Promise<ChatResponse>;
  isGenerating: boolean;
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const addMessage = useCallback((text: string, sender: 'user' | 'assistant') => {
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const generateResponse = useCallback(async (text: string): Promise<ChatResponse> => {
    try {
      setIsGenerating(true);
      const response = await fetch('/api/v1/chat/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat generation failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      return {
        success: true,
        message: result.message,
      };
    } catch (error) {
      console.error('Chat generation error:', error);
      return {
        success: false,
        message: '',
        error: error instanceof Error ? error.message : 'Failed to generate response',
      };
    } finally {
      setIsGenerating(false);
    }
  }, []);

  return {
    messages,
    addMessage,
    clearMessages,
    generateResponse,
    isGenerating,
  };
}; 