/**
 * frontend/src/components/LanguageSelector.tsx
 *
 * Startup language selector — shown before first chat interaction.
 */
'use client';

import { Globe } from 'lucide-react';
import { useLanguage, Language } from '@/context/LanguageContext';

const OPTIONS: { id: Language; label: string; description: string; example: string }[] = [
  {
    id: 'mr',
    label: 'मराठी',
    description: 'प्रश्न आणि उत्तरे मराठीत',
    example: 'शेतीबद्दल काय सांगितलं आहे?',
  },
  {
    id: 'en',
    label: 'English',
    description: 'Ask in English, answers in English over Marathi transcripts',
    example: 'What is discussed about farming?',
  },
];

export default function LanguageSelector() {
  const { confirmLanguage } = useLanguage();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-900/95 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg mx-4">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-brand-500/20">
            <Globe className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-2xl font-semibold text-white mb-2">Select Language</h2>
          <p className="text-slate-400 text-sm">Choose your preferred language for questions and answers</p>
        </div>

        <div className="space-y-3">
          {OPTIONS.map((opt) => (
            <button
              key={opt.id}
              onClick={() => confirmLanguage(opt.id)}
              className="w-full text-left bg-surface-700 border border-surface-600 hover:border-brand-500 hover:bg-surface-700/80 rounded-xl p-5 transition-all duration-200 group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-lg font-semibold text-white group-hover:text-brand-300 transition-colors">
                  {opt.label}
                </span>
                <span className="text-xs text-slate-500 uppercase tracking-wider">{opt.id}</span>
              </div>
              <p className="text-sm text-slate-400 mb-2">{opt.description}</p>
              <p className="text-xs text-slate-500 italic font-['Noto_Sans_Devanagari',_sans-serif]">
                e.g. {opt.example}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
