/**
 * frontend/src/context/LanguageContext.tsx
 *
 * Language preference for the RAG chatbot.
 * mr = Marathi Q&A, en = English Q&A over Marathi transcripts.
 */
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Language = 'mr' | 'en';

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  isSelected: boolean;
  confirmLanguage: (lang: Language) => void;
}

const STORAGE_KEY = 'marathi-rag-language';

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('mr');
  const [isSelected, setIsSelected] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Language | null;
    if (stored === 'mr' || stored === 'en') {
      setLanguageState(stored);
      setIsSelected(true);
    }
  }, []);

  const confirmLanguage = (lang: Language) => {
    setLanguageState(lang);
    setIsSelected(true);
    localStorage.setItem(STORAGE_KEY, lang);
  };

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(STORAGE_KEY, lang);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, isSelected, confirmLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}
