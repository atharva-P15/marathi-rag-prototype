"""
backend/services/asr/whisper_service.py

OpenAI Whisper ASR service for Marathi speech-to-text.
Uses word-level timestamps to enable precise chunk time attribution.

Production swap: Replace the transcribe() implementation with a call to
Whisper API or AssemblyAI. The return format (list of segment dicts)
stays identical so downstream services don't change.
"""
import json
import logging
import whisper
from pathlib import Path
from backend.config import settings

logger = logging.getLogger(__name__)

# Module-level model cache — loaded once, reused for every call
_model: whisper.Whisper | None = None


def _load_model() -> whisper.Whisper:
    """Load Whisper model (lazy, cached). Downloads on first call."""
    global _model
    if _model is None:
        logger.info(f"Loading Whisper model: {settings.whisper_model} ...")
        _model = whisper.load_model(settings.whisper_model)
        logger.info("Whisper model loaded.")
    return _model


def transcribe(audio_path: str, save_dir: str | None = None) -> dict:
    """
    Transcribe a WAV audio file using Whisper with segment-level timestamps.

    Args:
        audio_path: Path to the 16kHz mono WAV file.
        save_dir:   If provided, saves raw transcript JSON here for inspection.

    Returns:
        Whisper result dict containing:
          - text: full transcript string
          - segments: list of { id, start, end, text, ... }
          - language: detected language code
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _load_model()

    logger.info(f"Transcribing: {audio_path.name} (language=Marathi forced)")

    result = model.transcribe(
        str(audio_path),
        language="mr",          # Force Marathi; avoids language detection overhead
        task="transcribe",      # 'transcribe' keeps original language; 'translate' → English
        verbose=False,
        word_timestamps=False,  # Segment-level is sufficient for chunking
    )

    logger.info(f"Transcription complete. Segments: {len(result['segments'])}")

    # Optionally persist raw transcript for debugging / re-processing
    if save_dir:
        save_path = Path(save_dir) / f"{audio_path.stem}_transcript.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Raw transcript saved: {save_path}")

    return result
