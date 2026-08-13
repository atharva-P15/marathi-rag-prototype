/**
 * frontend/src/components/FollowUpSuggestions.tsx
 *
 * Clickable follow-up question chips displayed below each assistant answer.
 */
'use client';

import { Lightbulb } from 'lucide-react';

interface FollowUpSuggestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export default function FollowUpSuggestions({ questions, onSelect }: FollowUpSuggestionsProps) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="mt-4 animate-fade-in">
      <div className="flex items-center gap-1.5 mb-2.5">
        <Lightbulb className="w-3.5 h-3.5 text-yellow-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Suggested Questions
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="
              text-sm text-slate-300 bg-surface-700 border border-surface-500
              hover:border-brand-500 hover:text-brand-300 hover:bg-brand-900/30
              px-3 py-1.5 rounded-full transition-all duration-200
              font-['Noto_Sans_Devanagari',_sans-serif] text-left
              active:scale-95 cursor-pointer
            "
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
