/**
 * frontend/src/components/SourceCard.tsx
 *
 * Displays a single retrieved source chunk with video name, timestamp,
 * similarity score, and excerpt text.
 */
'use client';

import { Clock, Film, BarChart2 } from 'lucide-react';
import { SourceChunk, formatTimestamp } from '@/lib/api';

interface SourceCardProps {
  source: SourceChunk;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const scorePercent = Math.round(source.score * 100);

  return (
    <div className="group relative bg-surface-700 border border-surface-600 rounded-xl p-4 hover:border-brand-500/50 transition-all duration-200 hover:shadow-lg hover:shadow-brand-500/10 animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-700/60 flex items-center justify-center text-brand-300 text-xs font-bold">
            {index + 1}
          </span>
          <div className="flex items-center gap-1.5 min-w-0">
            <Film className="w-3.5 h-3.5 text-brand-400 flex-shrink-0" />
            <span className="text-sm font-medium text-white truncate">{source.video_name}</span>
          </div>
        </div>

        {/* Similarity score badge */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <BarChart2 className="w-3 h-3 text-emerald-400" />
          <span className="text-xs font-semibold text-emerald-400">{scorePercent}%</span>
        </div>
      </div>

      {/* Timestamp */}
      <div className="flex items-center gap-1.5 mb-3">
        <Clock className="w-3.5 h-3.5 text-amber-400" />
        <span className="text-xs font-mono text-amber-300 bg-amber-400/10 px-2 py-0.5 rounded-md border border-amber-400/20">
          {formatTimestamp(source.start_time)} – {formatTimestamp(source.end_time)}
        </span>
      </div>

      {/* Text excerpt */}
      <p className="text-sm text-slate-300 leading-relaxed line-clamp-3 font-['Noto_Sans_Devanagari',_sans-serif]">
        {source.text}
      </p>
    </div>
  );
}
