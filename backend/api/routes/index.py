"""
backend/api/routes/index.py

POST /index — Trigger the full indexing pipeline for a single video.

Flow:
  1. Extract audio (FFmpeg)
  2. Transcribe (Whisper)
  3. Clean transcript
  4. Chunk with timestamps
  5. Generate embeddings (bge-m3)
  6. Store in ChromaDB + SQLite
"""
import uuid
import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.api.schemas.video import IndexRequest, IndexResponse
from backend.database.sqlite_client import get_db
from backend.database.chroma_client import get_collection
from backend.database.models import Video, Chunk
from backend.utils.audio_extractor import extract_audio, NoAudioStreamError
from backend.services.asr.whisper_service import transcribe
from backend.services.chunker.chunker_service import chunk_transcript
from backend.services.embedder.embedder_service import embed_texts
from backend.services.retriever.bm25_index import rebuild_index
from backend.utils.indexing_helpers import build_embedding_text, build_chroma_metadata
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/index", response_model=IndexResponse, summary="Index a video through the full pipeline")
def index_video(request: IndexRequest, db: Session = Depends(get_db)) -> IndexResponse:
    """
    Run the complete indexing pipeline for a video file.
    The video must already exist at the specified path.
    """
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video not found: {request.video_path}")

    video_id = str(uuid.uuid4())
    video_name = video_path.stem

    # Persist video record immediately (status=pending)
    video_record = Video(
        id=video_id,
        name=video_name,
        filename=video_path.name,
        status="pending",
    )
    db.add(video_record)
    db.commit()

    try:
        # --- Step 1: Audio extraction ---
        logger.info(f"[{video_name}] Step 1/5: Extracting audio...")
        wav_path = extract_audio(str(video_path), settings.media_audio_dir)

        # --- Step 2: ASR (Whisper) ---
        logger.info(f"[{video_name}] Step 2/5: Transcribing audio...")
        transcript_result = transcribe(wav_path, save_dir=settings.media_transcripts_dir)
        segments = transcript_result.get("segments", [])
        duration = segments[-1]["end"] if segments else 0.0

        # --- Step 3 & 4: Clean + Chunk ---
        logger.info(f"[{video_name}] Step 3/5: Chunking transcript...")
        chunks = chunk_transcript(
            segments=segments,
            video_id=video_id,
            video_name=video_name,
            save_dir=settings.media_chunks_dir,
        )

        if not chunks:
            raise ValueError("No chunks were generated. Check the transcript.")

        # --- Step 5a: Generate embeddings ---
        logger.info(f"[{video_name}] Step 4/5: Generating embeddings for {len(chunks)} chunks...")
        embedding_texts = [build_embedding_text(c) for c in chunks]
        embeddings = embed_texts(embedding_texts)

        # --- Step 5b: Store in ChromaDB ---
        logger.info(f"[{video_name}] Step 5/5: Storing in ChromaDB + SQLite...")
        collection = get_collection()
        collection.add(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[build_chroma_metadata(c) for c in chunks],
        )

        # --- Store chunks in SQLite ---
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

        # Update video record to indexed
        video_record.status = "indexed"
        video_record.duration = duration
        video_record.indexed_at = datetime.utcnow()
        db.commit()

        rebuild_index()

        logger.info(f"[{video_name}] Indexing complete. {len(chunks)} chunks stored.")

        return IndexResponse(
            video_id=video_id,
            video_name=video_name,
            chunks_indexed=len(chunks),
            status="success",
        )

    except NoAudioStreamError as e:
        logger.error(f"[{video_name}] No audio stream: {e}")
        video_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"[{video_name}] Indexing failed")
        video_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
