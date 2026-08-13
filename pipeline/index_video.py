#!/usr/bin/env python3
"""
pipeline/index_video.py

One-command indexing pipeline for a single Marathi video.

Usage:
    python pipeline/index_video.py --video media/videos/sample.mp4
    python pipeline/index_video.py --video media/videos/sample.mp4 --force

This script mirrors exactly what the POST /index API endpoint does,
but is designed for CLI use (e.g., batch scripting in production).

Architecture note:
    In production, this logic moves to a Celery/Kafka worker.
    The service functions called here remain identical.
"""
import sys
import argparse
import logging
import uuid
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

# Add project root to Python path so we can import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.database.sqlite_client import init_db, SessionLocal
from backend.database.chroma_client import get_collection
from backend.database.models import Video, Chunk
from backend.utils.audio_extractor import extract_audio, NoAudioStreamError
from backend.services.asr.whisper_service import transcribe
from backend.services.chunker.chunker_service import chunk_transcript
from backend.services.embedder.embedder_service import embed_texts
from backend.services.retriever.bm25_index import rebuild_index
from backend.utils.indexing_helpers import build_embedding_text, build_chroma_metadata

console = Console()
logging.basicConfig(level=logging.WARNING)  # Suppress verbose library logs in CLI


def parse_args():
    parser = argparse.ArgumentParser(
        description="Index a Marathi video into the RAG pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline/index_video.py --video media/videos/my_video.mp4
  python pipeline/index_video.py --video media/videos/my_video.mp4 --whisper-model large-v3
        """,
    )
    parser.add_argument(
        "--video", required=True,
        help="Path to the video file (relative or absolute)"
    )
    parser.add_argument(
        "--whisper-model", default=None,
        help="Override Whisper model (tiny/base/small/medium/large-v2/large-v3)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-index even if this video was already indexed"
    )
    return parser.parse_args()


def run_pipeline(video_path: Path, force: bool = False):
    """Execute the full indexing pipeline with rich CLI output."""

    # Override whisper model if specified via CLI
    console.print(Panel.fit(
        f"[bold cyan]Marathi RAG — Indexing Pipeline[/bold cyan]\n"
        f"Video: [yellow]{video_path.name}[/yellow]",
        border_style="cyan",
    ))

    settings.ensure_dirs()
    init_db()

    db = SessionLocal()

    try:
        # Check if already indexed
        existing = db.query(Video).filter(Video.filename == video_path.name).first()
        if existing and existing.status == "indexed" and not force:
            console.print(f"[yellow]⚠ Video already indexed (ID: {existing.id}). Use --force to re-index.[/yellow]")
            return

        video_id = str(uuid.uuid4())
        video_name = video_path.stem

        video_record = Video(
            id=video_id,
            name=video_name,
            filename=video_path.name,
            status="pending",
        )
        db.add(video_record)
        db.commit()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            # --- Step 1: Audio Extraction ---
            task = progress.add_task("[cyan]Step 1/5 · Extracting audio (FFmpeg)...", total=None)
            wav_path = extract_audio(str(video_path), settings.media_audio_dir)
            progress.update(task, description=f"[green]✓ Step 1/5 · Audio extracted → {Path(wav_path).name}")
            progress.stop_task(task)

            # --- Step 2: ASR ---
            task = progress.add_task(
                f"[cyan]Step 2/5 · Transcribing with Whisper ({settings.whisper_model})...", total=None
            )
            transcript_result = transcribe(wav_path, save_dir=settings.media_transcripts_dir)
            segments = transcript_result.get("segments", [])
            duration = segments[-1]["end"] if segments else 0.0
            progress.update(task, description=f"[green]✓ Step 2/5 · Transcription complete ({len(segments)} segments)")
            progress.stop_task(task)

            # --- Step 3 & 4: Clean + Chunk ---
            task = progress.add_task("[cyan]Step 3/5 · Cleaning & chunking transcript...", total=None)
            chunks = chunk_transcript(
                segments=segments,
                video_id=video_id,
                video_name=video_name,
                save_dir=settings.media_chunks_dir,
            )
            progress.update(task, description=f"[green]✓ Step 3/5 · {len(chunks)} chunks created")
            progress.stop_task(task)

            if not chunks:
                console.print("[red]✗ No chunks generated. Aborting.[/red]")
                video_record.status = "failed"
                db.commit()
                return

            # --- Step 5: Embeddings ---
            task = progress.add_task(f"[cyan]Step 4/5 · Generating embeddings (bge-m3, {len(chunks)} chunks)...", total=None)
            embedding_texts = [build_embedding_text(c) for c in chunks]
            embeddings = embed_texts(embedding_texts)
            progress.update(task, description=f"[green]✓ Step 4/5 · Embeddings generated (dim={len(embeddings[0])})")
            progress.stop_task(task)

            # --- Step 6: Store ---
            task = progress.add_task("[cyan]Step 5/5 · Storing in ChromaDB + SQLite...", total=None)

            collection = get_collection()
            collection.add(
                ids=[c.id for c in chunks],
                embeddings=embeddings,
                documents=[c.text for c in chunks],
                metadatas=[build_chroma_metadata(c) for c in chunks],
            )

            for chunk in chunks:
                db.add(Chunk(
                    id=chunk.id,
                    video_id=chunk.video_id,
                    chunk_index=chunk.chunk_index,
                    start_time=chunk.start_time,
                    end_time=chunk.end_time,
                    text=chunk.text,
                    char_count=len(chunk.text),
                ))

            video_record.status = "indexed"
            video_record.duration = duration
            video_record.indexed_at = datetime.utcnow()
            db.commit()

            rebuild_index()

            progress.update(task, description="[green]✓ Step 5/5 · Stored in ChromaDB + SQLite")
            progress.stop_task(task)

        # --- Summary Table ---
        table = Table(title="[bold green]✓ Indexing Complete[/bold green]", border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Video ID", video_id)
        table.add_row("Video Name", video_name)
        table.add_row("Duration", f"{duration:.1f}s ({duration/60:.1f} min)")
        table.add_row("Segments", str(len(segments)))
        table.add_row("Chunks Indexed", str(len(chunks)))
        table.add_row("Embedding Dim", str(len(embeddings[0])))
        table.add_row("ChromaDB Collection", settings.chroma_collection_name)
        console.print(table)
        console.print("\n[bold]You can now ask questions:[/bold]")
        console.print("  → Start the backend: [cyan]uvicorn backend.main:app --reload[/cyan]")
        console.print("  → Start the frontend: [cyan]cd frontend && npm run dev[/cyan]")

    except NoAudioStreamError as e:
        console.print(f"\n[bold red]✗ Cannot index: {e}[/bold red]")
        if 'video_record' in locals():
            video_record.status = "failed"
            db.commit()
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Indexing failed: {e}[/bold red]")
        if 'video_record' in locals():
            video_record.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    args = parse_args()
    video_path = Path(args.video)

    if not video_path.exists():
        console.print(f"[red]✗ Video file not found: {video_path}[/red]")
        sys.exit(1)

    # Override whisper model from CLI arg if provided
    if args.whisper_model:
        settings.whisper_model = args.whisper_model

    run_pipeline(video_path, force=args.force)
