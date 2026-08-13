/**
 * frontend/src/lib/api.ts
 *
 * Typed API client for the FastAPI backend.
 * All fetch calls go through here — easy to swap base URL in production.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type Language = 'mr' | 'en';

export interface SourceChunk {
  chunk_id: string;
  video_name: string;
  start_time: number;
  end_time: number;
  text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  follow_up_questions: string[];
  language: Language;
}

export interface VideoInfo {
  id: string;
  name: string;
  filename: string;
  duration: number | null;
  language: string;
  status: string;
  indexed_at: string | null;
}

export async function sendChatMessage(
  question: string,
  language: Language = 'mr',
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, language }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Chat API error: ${err}`);
  }
  return res.json();
}

export async function listVideos(): Promise<VideoInfo[]> {
  const res = await fetch(`${API_BASE}/api/v1/videos`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  return res.json();
}

export function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
