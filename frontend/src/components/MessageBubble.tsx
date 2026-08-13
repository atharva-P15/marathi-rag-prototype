/**
 * frontend/src/components/MessageBubble.tsx
 *
 * Renders a single chat message (user or assistant).
 * Assistant messages include source cards and follow-up suggestions.
 */
'use client';

import { User, Bot, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Message } from '@/hooks/useChat';
import SourceCard from './SourceCard';
import FollowUpSuggestions from './FollowUpSuggestions';

interface MessageBubbleProps {
  message: Message;
  onFollowUp: (question: string) => void;
}

export default function MessageBubble({ message, onFollowUp }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser
          ? 'bg-brand-600'
          : 'bg-gradient-to-br from-purple-600 to-brand-600'
      }`}>
        {isUser
          ? <User className="w-4 h-4 text-white" />
          : <Bot className="w-4 h-4 text-white" />
        }
      </div>

      {/* Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        {/* Message bubble */}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-surface-700 border border-surface-600 text-slate-100 rounded-tl-sm'
        }`}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap font-['Noto_Sans_Devanagari',_Inter,_sans-serif]">
            {message.content}
          </p>
        </div>

        {/* Source toggle (only for assistant) */}
        {!isUser && hasSources && (
          <button
            onClick={() => setShowSources((s) => !s)}
            className="
              flex items-center gap-1.5 text-xs text-slate-400
              hover:text-brand-400 transition-colors duration-150
              bg-surface-800 border border-surface-600 rounded-full px-3 py-1
              hover:border-brand-600
            "
          >
            {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showSources ? 'Hide' : 'Show'} {message.sources!.length} source{message.sources!.length > 1 ? 's' : ''}
          </button>
        )}

        {/* Source cards */}
        {!isUser && showSources && hasSources && (
          <div className="w-full grid gap-2">
            {message.sources!.map((source, i) => (
              <SourceCard key={source.chunk_id} source={source} index={i} />
            ))}
          </div>
        )}

        {/* Follow-up suggestions */}
        {!isUser && message.followUpQuestions && (
          <div className="w-full">
            <FollowUpSuggestions
              questions={message.followUpQuestions}
              onSelect={onFollowUp}
            />
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[11px] text-slate-600">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
