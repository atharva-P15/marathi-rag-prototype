/**
 * frontend/src/app/page.tsx
 *
 * Main page — full-height chat layout with sidebar showing indexed videos.
 */
'use client';

import { useEffect, useState } from 'react';
import { Database, Video, CheckCircle2, Clock, AlertCircle, Globe } from 'lucide-react';
import ChatWindow from '@/components/ChatWindow';
import LanguageSelector from '@/components/LanguageSelector';
import { useLanguage } from '@/context/LanguageContext';
import { listVideos, VideoInfo, formatTimestamp } from '@/lib/api';

function VideoStatusIcon({ status }: { status: string }) {
  if (status === 'indexed') return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
  if (status === 'pending') return <Clock className="w-3.5 h-3.5 text-amber-400" />;
  return <AlertCircle className="w-3.5 h-3.5 text-red-400" />;
}

export default function HomePage() {
  const { language, setLanguage, isSelected } = useLanguage();
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    listVideos()
      .then(setVideos)
      .catch(() => setVideos([]));
  }, []);

  return (
    <>
      {!isSelected && <LanguageSelector />}

      <div className="flex h-screen bg-surface-900 overflow-hidden">
        {sidebarOpen && (
          <aside className="w-64 flex-shrink-0 bg-surface-800 border-r border-surface-700 flex flex-col">
            <div className="p-4 border-b border-surface-700">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-600 to-purple-600 flex items-center justify-center">
                  <Database className="w-4 h-4 text-white" />
                </div>
                <h2 className="font-semibold text-white text-sm">Indexed Videos</h2>
              </div>
              <p className="text-xs text-slate-500 pl-9">{videos.length} video{videos.length !== 1 ? 's' : ''}</p>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {videos.length === 0 ? (
                <div className="text-center py-8">
                  <Video className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-xs text-slate-500">No videos indexed yet.</p>
                  <p className="text-xs text-slate-600 mt-1">Run the pipeline to get started.</p>
                </div>
              ) : (
                videos.map((v) => (
                  <div
                    key={v.id}
                    className="bg-surface-700 border border-surface-600 rounded-xl p-3 hover:border-brand-600/50 transition-all duration-200"
                  >
                    <div className="flex items-start gap-2">
                      <VideoStatusIcon status={v.status} />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white truncate">{v.name}</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-xs text-slate-500">{v.language.toUpperCase()}</span>
                          {v.duration && (
                            <>
                              <span className="text-slate-600">·</span>
                              <span className="text-xs text-slate-500 font-mono">
                                {formatTimestamp(v.duration)}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t border-surface-700 space-y-2">
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as 'mr' | 'en')}
                  className="flex-1 bg-surface-700 border border-surface-600 text-xs text-slate-300 rounded-lg px-2 py-1.5 focus:outline-none focus:border-brand-500"
                >
                  <option value="mr">मराठी (Marathi)</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Backend: localhost:8000
              </div>
            </div>
          </aside>
        )}

        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between px-6 py-3 border-b border-surface-700 bg-surface-800 flex-shrink-0">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen((o) => !o)}
                className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-surface-700"
                aria-label="Toggle sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h1 className="text-base font-semibold text-white">
                  {language === 'mr' ? 'मराठी मीडिया RAG' : 'Marathi Media RAG'}
                </h1>
                <p className="text-xs text-slate-500">
                  {language === 'mr'
                    ? 'Hybrid search · Semantic chunking · Marathi Q&A'
                    : 'English answers over Marathi transcripts'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-surface-700 text-slate-400 uppercase">
                {language}
              </span>
              <span className="text-xs text-slate-500 hidden sm:block">Powered by</span>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium text-brand-400">Groq</span>
                <span className="text-slate-600 text-xs">·</span>
                <span className="text-xs font-medium text-purple-400">bge-m3</span>
                <span className="text-slate-600 text-xs">·</span>
                <span className="text-xs font-medium text-emerald-400">Hybrid</span>
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-hidden">
            <ChatWindow />
          </div>
        </div>
      </div>
    </>
  );
}
