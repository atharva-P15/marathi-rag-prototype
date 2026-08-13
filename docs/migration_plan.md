# Marathi Media RAG Prototype — Migration Plan

## Prototype → Production Component Swap Guide

Each prototype component is designed with a thin interface so production
equivalents can replace it with minimal code changes.

---

## 1. Vector Store: ChromaDB → Qdrant

**Files to change**: `backend/database/chroma_client.py`

Create `backend/database/qdrant_client.py` implementing the same interface:

```python
# Same interface, different implementation
def get_collection() -> QdrantCollection:
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return client.get_or_create_collection(name=settings.collection_name, ...)
```

No other files change — `retriever_service.py` and `index.py` call `get_collection()`.

---

## 2. Metadata DB: SQLite → PostgreSQL

**Files to change**: `backend/database/sqlite_client.py`

Change one line:
```python
# Before (SQLite)
url = f"sqlite:///{db_path}"

# After (PostgreSQL)
url = f"postgresql://{user}:{password}@{host}/{dbname}"
```

SQLAlchemy ORM models in `models.py` stay 100% identical.

---

## 3. Storage: Local files → Object Storage

**Files to change**: `backend/utils/audio_extractor.py`

Wrap `extract_audio()` to upload result to S3:
```python
# After extraction, upload to S3
s3_client.upload_file(wav_path, bucket, key)
return s3_uri  # Return S3 URI instead of local path
```

---

## 4. ASR: Whisper local → Whisper API / AssemblyAI

**Files to change**: `backend/services/asr/whisper_service.py`

```python
# Replace local model.transcribe() with:
import openai
result = openai.audio.transcriptions.create(
    model="whisper-1",
    file=open(audio_path, "rb"),
    response_format="verbose_json",
    timestamp_granularities=["segment"],
)
```

Return format stays identical — downstream chunker doesn't change.

---

## 5. Single video → Batch processing

Add Celery task queue:
```python
# pipeline/tasks.py
from celery import Celery
app = Celery('marathi_rag', broker='redis://localhost:6379/0')

@app.task
def index_video_task(video_path: str):
    run_pipeline(Path(video_path))
```

The `run_pipeline()` function from `index_video.py` remains unchanged.

---

## 6. No auth → OAuth2 / API Key auth

Add FastAPI middleware:
```python
# backend/middleware/auth.py
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

Add `Depends(get_current_user)` to protected routes.

---

## 7. No memory → Conversation memory

Add conversation table to SQLite:
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    messages JSON,
    created_at DATETIME
);
```

Inject last N turns into Groq's prompt in `groq_service.py`.

---

## Summary: What NEVER changes

| Component | Stays same |
|---|---|
| FastAPI routes | ✓ |
| Pydantic schemas | ✓ |
| SQLAlchemy models | ✓ |
| Chunker service | ✓ |
| Embedder service | ✓ |
| Groq service | ✓ |
| Frontend | ✓ |
| Prompt template | ✓ |
| Pipeline script logic | ✓ |
