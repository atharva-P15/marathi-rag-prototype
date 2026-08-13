/**
 * frontend/src/components/ChatWindow.tsx
 *
 * Main chat interface component.
 * Handles auto-scroll, input, loading state, and error display.
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { Send, Trash2, Mic } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { useLanguage } from '@/context/LanguageContext';
import MessageBubble from './MessageBubble';

const EXAMPLE_QUESTIONS = {
  mr: [
    'शेतीबद्दल काय सांगितलं आहे?',
    'मुख्य विषय काय आहे?',
    'कोणत्या समस्यांवर चर्चा झाली?',
    'महत्त्वाचे मुद्दे सांगा.',
  ],
  en: [
    'What is discussed about farming?',
    'What are the main topics covered?',
    'What problems were mentioned?',
    'Summarize the key points.',
  ],
};

export default function ChatWindow() {
  const { language } = useLanguage();
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const examples = EXAMPLE_QUESTIONS[language];
  const placeholder =
    language === 'mr'
      ? 'प्रश्न विचारा... (Ask in Marathi)'
      : 'Ask a question in English...';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || isLoading) return;
    setInput('');
    await sendMessage(q);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFollowUp = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 scrollbar-thin scrollbar-thumb-surface-600">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-600 to-purple-600 flex items-center justify-center shadow-xl shadow-brand-500/20">
              <Mic className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white mb-2">
                {language === 'mr' ? 'मराठी मीडिया RAG' : 'Marathi Media RAG'}
              </h3>
              <p className="text-slate-400 text-sm max-w-sm leading-relaxed">
                {language === 'mr'
                  ? 'इंडेक्स केलेल्या मराठी व्हिडिओ सामग्रीबद्दल प्रश्न विचारा.'
                  : 'Ask questions about indexed Marathi video content. Answers in English.'}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 w-full max-w-lg">
              {examples.map((q) => (
                <button
                  key={q}
                  onClick={() => handleFollowUp(q)}
                  className="text-sm text-left text-slate-300 bg-surface-700 border border-surface-600 hover:border-brand-500 hover:text-brand-300 px-4 py-3 rounded-xl transition-all duration-200 font-['Noto_Sans_Devanagari',_Inter,_sans-serif]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onFollowUp={handleFollowUp}
          />
        ))}

        {isLoading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-brand-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs">AI</span>
            </div>
            <div className="bg-surface-700 border border-surface-600 rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-1.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot"
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm animate-fade-in">
            ⚠ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t border-surface-700 p-4 bg-surface-800">
        {messages.length > 0 && (
          <div className="flex justify-end mb-2">
            <button
              onClick={clearMessages}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors duration-150"
            >
              <Trash2 className="w-3 h-3" />
              Clear chat
            </button>
          </div>
        )}
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={isLoading}
            className="
              flex-1 bg-surface-700 border border-surface-500 rounded-xl
              px-4 py-3 text-sm text-white placeholder-slate-500
              focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50
              resize-none transition-all duration-200 min-h-[48px] max-h-[160px]
              font-['Noto_Sans_Devanagari',_Inter,_sans-serif]
              disabled:opacity-50
            "
            style={{ height: 'auto' }}
            onInput={(e) => {
              const t = e.currentTarget;
              t.style.height = 'auto';
              t.style.height = `${Math.min(t.scrollHeight, 160)}px`;
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            id="send-button"
            className="
              flex-shrink-0 w-12 h-12 rounded-xl
              bg-brand-600 hover:bg-brand-500
              disabled:opacity-40 disabled:cursor-not-allowed
              flex items-center justify-center
              transition-all duration-200 active:scale-95
              shadow-lg shadow-brand-500/20
            "
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
        <p className="text-[11px] text-slate-600 mt-2 text-center">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
