"""
backend/services/chunker/chunker_service.py

Semantic, topic-aware chunker for Whisper transcript segments.

Strategy:
  - Respect topic boundaries and speaker turns from preprocessing.
  - Split at sentence boundaries when possible.
  - Target CHUNK_WORD_LIMIT words with CHUNK_OVERLAP_WORDS overlap.
  - Attach keywords and speaker metadata for retrieval enrichment.
"""
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Set

from backend.config import settings
from backend.utils.transcript_cleaner import clean_segments
from backend.utils.marathi_text import extract_keywords

logger = logging.getLogger(__name__)


@dataclass
class TranscriptChunk:
    """A single timestamped chunk of transcript text."""
    id: str
    video_id: str
    video_name: str
    chunk_index: int
    start_time: float
    end_time: float
    text: str
    keywords: List[str] = field(default_factory=list)
    speaker_turns: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _word_count(text: str) -> int:
    return len(text.split())


def _build_chunk_text(segments: List[dict]) -> str:
    """Join segments with speaker markers at turn changes."""
    parts: List[str] = []
    prev_turn = None
    for seg in segments:
        turn = seg.get("speaker_turn", 0)
        if prev_turn is not None and turn != prev_turn:
            parts.append(f"[Speaker {turn + 1}]")
        parts.append(seg["text"])
        prev_turn = turn
    return " ".join(parts).strip()


def _collect_speaker_turns(segments: List[dict]) -> List[int]:
    turns: Set[int] = set()
    for seg in segments:
        turns.add(seg.get("speaker_turn", 0))
    return sorted(turns)


def _find_split_point(segments: List[dict], word_limit: int) -> int:
    """
    Find the best split index respecting topic boundaries and sentence ends.
    Returns the number of segments to include (at least 1).
    """
    word_count = 0
    best_split = 1

    for i, seg in enumerate(segments):
        word_count += _word_count(seg["text"])
        if word_count >= word_limit:
            # Prefer splitting at topic boundary or sentence end
            if seg.get("topic_boundary") or seg.get("is_sentence_end"):
                return i + 1
            best_split = i + 1
            break
        best_split = i + 1

    return max(1, best_split)


def _overlap_start(segments: List[dict], end_idx: int, overlap_words: int) -> int:
    """Walk backwards from end_idx to find overlap start by word count."""
    words = 0
    start = end_idx
    for i in range(end_idx - 1, -1, -1):
        words += _word_count(segments[i]["text"])
        start = i
        if words >= overlap_words:
            break
    return start


def chunk_transcript(
    segments: List[dict],
    video_id: str,
    video_name: str,
    save_dir: str | None = None,
) -> List[TranscriptChunk]:
    """
    Convert Whisper segments into semantic, timestamp-aware chunks.

    Args:
        segments:   Raw Whisper segments [{ start, end, text }]
        video_id:   UUID of the video record in SQLite
        video_name: Human-readable video name (shown in citations)
        save_dir:   If provided, saves chunk JSON here for inspection

    Returns:
        List of TranscriptChunk objects ready for embedding + storage.
    """
    word_limit = settings.chunk_word_limit
    overlap_words = settings.chunk_overlap_words
    min_words = settings.chunk_min_words

    cleaned_segments = clean_segments(segments)
    if not cleaned_segments:
        return []

    chunks: List[TranscriptChunk] = []
    chunk_index = 0
    i = 0

    while i < len(cleaned_segments):
        remaining = cleaned_segments[i:]

        # Force split at topic boundaries for the first segment in remaining
        if remaining[0].get("topic_boundary") and i > 0:
            # Topic boundary already handled by starting fresh at i
            pass

        split_count = _find_split_point(remaining, word_limit)
        current_segs = remaining[:split_count]

        chunk_text = _build_chunk_text(current_segs)
        if _word_count(chunk_text) < min_words and split_count < len(remaining):
            # Extend to meet minimum if possible
            extended = remaining[: min(split_count + 2, len(remaining))]
            chunk_text = _build_chunk_text(extended)
            current_segs = extended

        if not chunk_text.strip():
            i += 1
            continue

        keywords = extract_keywords(chunk_text, top_n=8)
        speaker_turns = _collect_speaker_turns(current_segs)

        chunk = TranscriptChunk(
            id=str(uuid.uuid4()),
            video_id=video_id,
            video_name=video_name,
            chunk_index=chunk_index,
            start_time=round(current_segs[0]["start"], 2),
            end_time=round(current_segs[-1]["end"], 2),
            text=chunk_text,
            keywords=keywords,
            speaker_turns=speaker_turns,
        )
        chunks.append(chunk)
        chunk_index += 1

        if split_count >= len(remaining):
            break

        # Overlap: start next chunk with overlapping segments
        next_start = i + split_count
        overlap_start = _overlap_start(cleaned_segments, next_start, overlap_words)
        i = max(i + 1, overlap_start)

    logger.info(
        f"Semantic chunking complete: {len(chunks)} chunks "
        f"from {len(cleaned_segments)} segments."
    )

    if save_dir:
        save_path = Path(save_dir) / f"{video_id}_chunks.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in chunks], f, ensure_ascii=False, indent=2)
        logger.info(f"Chunks saved: {save_path}")

    return chunks
