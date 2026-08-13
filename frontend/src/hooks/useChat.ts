/**
 * frontend/src/hooks/useChat.ts
 *
 * Custom hook managing chat state: messages, loading, and error handling.
 */
'use client';

import { useState, useCallback } from 'react';
import { sendChatMessage, ChatResponse, SourceChunk } from '@/lib/api';
import { useLanguage } from '@/context/LanguageContext';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceChunk[];
  followUpQuestions?: string[];
  timestamp: Date;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (question: string) => Promise<void>;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const { language } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await sendChatMessage(question.trim(), language);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        followUpQuestions: response.follow_up_questions,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, language]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearMessages };
}
