"""
backend/utils/transcript_cleaner.py

Enhanced Marathi transcript preprocessing before chunking and embedding.

Handles:
  - ASR artifact removal and Devanagari normalization
  - Repeated-word deduplication (common Whisper artifact)
  - Filler word trimming at segment edges
  - Pause-based sentence boundary detection
  - Pseudo speaker-turn segmentation via long inter-segment pauses
  - Punctuation restoration at natural pauses
  - Short segment merging for better discourse continuity
"""
import logging
import re
from typing import List

from backend.utils.marathi_text import normalize_devanagari, restore_punctuation

logger = logging.getLogger(__name__)

# Gaps (seconds) used for discourse structure heuristics
PAUSE_SENTENCE_SEC = 0.55
PAUSE_SPEAKER_SEC = 2.0
PAUSE_TOPIC_SEC = 4.0

ASR_MARKER_RE = re.compile(r"\[.*?\]|\(.*?\)|\{.*?\}")
REPEAT_WORD_RE = re.compile(r"\b(\w+)(?:\s+\1\b)+", re.UNICODE)
MULTI_SPACE_RE = re.compile(r"\s+")
MULTI_PUNCT_RE = re.compile(r"([.!?,।])\1+")
# Common Whisper hallucination patterns
HALLUCINATION_RE = re.compile(
    r"^(thank you|thanks for watching|subscribe|like and subscribe|"
    r"please subscribe|the end|music|applause|\.\.\.)[\s.!]*$",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    """Clean a single Whisper segment string."""
    text = normalize_devanagari(text)
    text = ASR_MARKER_RE.sub("", text)
    text = text.replace("\r\n", " ").replace("\n", " ")
    text = MULTI_SPACE_RE.sub(" ", text)
    text = MULTI_PUNCT_RE.sub(r"\1", text)
    text = REPEAT_WORD_RE.sub(r"\1", text)
    return text.strip()


def _trim_edge_fillers(text: str) -> str:
    """Remove common disfluency tokens at segment boundaries."""
    fillers = {"अं", "अ", "हं", "ह", "uh", "um", "hmm", "म्हणजे", "बरं"}
    words = text.split()
    while words and words[0].lower() in fillers:
        words.pop(0)
    while words and words[-1].lower() in fillers:
        words.pop()
    return " ".join(words)


def _gap(prev_end: float, curr_start: float) -> float:
    return max(0.0, curr_start - prev_end)


def _merge_short_segments(segments: List[dict], min_words: int = 3) -> List[dict]:
    """Merge very short segments with the previous one for better continuity."""
    if not segments:
        return []

    merged: List[dict] = []
    for seg in segments:
        word_count = len(seg["text"].split())
        if merged and word_count < min_words:
            prev = merged[-1]
            prev["text"] = f"{prev['text']} {seg['text']}".strip()
            prev["end"] = seg["end"]
            prev["is_sentence_end"] = seg.get("is_sentence_end", False)
        else:
            merged.append(dict(seg))
    return merged


def preprocess_segments(segments: List[dict]) -> List[dict]:
    """
    Full preprocessing pipeline for Whisper segments.

    Returns enriched segments with:
      - cleaned text with restored punctuation
      - is_sentence_end: bool
      - speaker_turn: int (pseudo speaker id from long pauses)
      - pause_before: float
      - topic_boundary: bool (long pause suggests topic shift)
    """
    if not segments:
        return []

    processed: List[dict] = []
    speaker_turn = 0

    for i, seg in enumerate(segments):
        text = _trim_edge_fillers(clean_text(seg.get("text", "")))
        if not text or HALLUCINATION_RE.match(text):
            continue

        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        pause_before = _gap(processed[-1]["end"], start) if processed else 0.0

        if pause_before >= PAUSE_SPEAKER_SEC:
            speaker_turn += 1

        topic_boundary = pause_before >= PAUSE_TOPIC_SEC
        is_sentence_end = pause_before >= PAUSE_SENTENCE_SEC or topic_boundary

        if is_sentence_end:
            text = restore_punctuation(text, is_sentence_end=True)

        processed.append({
            **seg,
            "start": start,
            "end": end,
            "text": text,
            "speaker_turn": speaker_turn,
            "pause_before": round(pause_before, 2),
            "is_sentence_end": is_sentence_end,
            "topic_boundary": topic_boundary,
        })

    processed = _merge_short_segments(processed)

    logger.info(
        f"Preprocessed {len(processed)} segments "
        f"({speaker_turn + 1} speaker turns detected)."
    )
    return processed


def clean_segments(segments: List[dict]) -> List[dict]:
    """Backward-compatible wrapper used by legacy callers."""
    return preprocess_segments(segments)
