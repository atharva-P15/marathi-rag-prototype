"""
backend/utils/audio_extractor.py

Extracts a mono 16kHz WAV audio track from a video file using FFmpeg.
Whisper requires 16kHz mono WAV for best results.

Production swap: Instead of writing to local disk, stream to object storage.
The function signature stays the same — only the output path changes.
"""
import json
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class NoAudioStreamError(ValueError):
    """Raised when the input file has no audio track to transcribe."""


def _probe_streams(video_path: Path) -> list[dict]:
    """Return stream metadata from ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed for {video_path.name}: {result.stderr.strip() or 'unknown error'}"
        )
    data = json.loads(result.stdout or "{}")
    return data.get("streams", [])


def has_audio_stream(video_path: str | Path) -> bool:
    """Check whether the file contains at least one audio stream."""
    streams = _probe_streams(Path(video_path))
    return any(s.get("codec_type") == "audio" for s in streams)


def get_stream_summary(video_path: str | Path) -> str:
    """Human-readable summary of streams in the file (for error messages)."""
    streams = _probe_streams(Path(video_path))
    if not streams:
        return "no streams detected"

    parts = []
    for s in streams:
        codec_type = s.get("codec_type", "unknown")
        codec = s.get("codec_name", "unknown")
        parts.append(f"{codec_type}/{codec}")
    return ", ".join(parts)


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract audio from a video file and save as a WAV file.

    Args:
        video_path: Absolute or relative path to the input video file.
        output_dir: Directory where the extracted WAV will be saved.

    Returns:
        Path to the extracted WAV file.

    Raises:
        FileNotFoundError: If the video file does not exist.
        NoAudioStreamError: If the file contains no audio track.
        RuntimeError: If FFmpeg fails.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if not has_audio_stream(video_path):
        summary = get_stream_summary(video_path)
        raise NoAudioStreamError(
            f"'{video_path.name}' has no audio track (streams: {summary}). "
            "Whisper transcription requires a video with an audio stream. "
            "Use a file that includes spoken audio, or re-export the recording with audio enabled."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_path = output_dir / f"{video_path.stem}.wav"

    if wav_path.exists():
        logger.info(f"Audio already extracted: {wav_path}. Skipping.")
        return str(wav_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-map", "0:a:0",         # First audio stream only
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(wav_path),
    ]

    logger.info(f"Extracting audio: {video_path.name} → {wav_path.name}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed with exit code {result.returncode}.\n"
            f"stderr: {result.stderr}"
        )

    logger.info(f"Audio extracted successfully: {wav_path}")
    return str(wav_path)
