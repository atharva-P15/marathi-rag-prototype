# मराठी मीडिया RAG — Marathi Media RAG Chatbot

> **Local prototype · Production-mirrored architecture · One Marathi video → Grounded answers with timestamps**

---

## What this is

A fully working local RAG (Retrieval-Augmented Generation) prototype that:

1. Extracts audio from a Marathi video using **FFmpeg**
2. Transcribes speech with **OpenAI Whisper** (Marathi language, timestamped)
3. Cleans and chunks the transcript with **timestamp-aware sliding window**
4. Generates multilingual embeddings with **BAAI/bge-m3**
5. Stores vectors in **ChromaDB** and metadata in **SQLite**
6. Answers questions in Marathi or English via **Groq API**
7. Returns grounded answers with **timestamps**, **source citations**, and **follow-up questions**

---

## Architecture

```
INDEXING PIPELINE
─────────────────
media/videos/*.mp4
    ↓ FFmpeg
media/audio/*.wav
    ↓ Whisper (Marathi)
Transcript segments [{start, end, text}]
    ↓ Cleaner + Chunker
Chunks [{chunk_id, start_time, end_time, text}]
    ↓ bge-m3 Embedder
Embeddings [float, 1024-dim]
    ↓              ↓
ChromaDB       SQLite
(vectors)    (metadata)


RETRIEVAL PIPELINE
──────────────────
User Question (Marathi / English)
    ↓ bge-m3 Embedder
Query Vector
    ↓ ChromaDB Semantic Search
Top-K Chunks + Timestamps
    ↓ Prompt Builder
Groq API
    ↓
Answer + Citations + Follow-up Questions
```

---

## Prerequisites

Install these before anything else:

### 1. Python 3.11+
Download from https://python.org/downloads/

Verify: `python --version`

### 2. Node.js 18+
Download from https://nodejs.org/

Verify: `node --version`

### 3. FFmpeg (Critical — required for audio extraction)

**Windows:**
```powershell
# Option A: Using winget (recommended)
winget install Gyan.FFmpeg

# Option B: Using Chocolatey
choco install ffmpeg

# Option C: Manual
# 1. Download from https://www.gyan.dev/ffmpeg/builds/
# 2. Extract to C:\ffmpeg\
# 3. Add C:\ffmpeg\bin to System PATH
```

Verify: `ffmpeg -version`

### 4. Git
Download from https://git-scm.com/

---

## Installation Guide

### Step 1 — Clone / Open the project

```powershell
cd marathi-rag-prototype
```

### Step 2 — Create Python virtual environment

```powershell
# Using pip (standard)
python -m venv .venv
.venv\Scripts\activate

# OR using uv (faster, recommended)
pip install uv
uv venv .venv
.venv\Scripts\activate
```

### Step 3 — Install Python dependencies

```powershell
# Using pip
pip install -r requirements.txt

# OR using uv
uv pip install -r requirements.txt
```

> ⚠ **First install downloads:**
> - Whisper model weights (~300MB for `medium`, ~1.5GB for `large-v3`)
> - BAAI/bge-m3 embedding model (~2.2GB)
> These are auto-cached after the first download.

### Step 4 — Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### Step 5 — Configure environment variables

```powershell
copy .env.example .env
# Now edit .env and add your GROQ_API_KEY
```

Edit `.env`:
```
GROQ_API_KEY=your-groq-api-key-here
WHISPER_MODEL=medium        # Use 'large-v3' for best accuracy (GPU recommended)
```

Get your Groq API key at: https://console.groq.com/keys

### Step 6 — Place your Marathi video

```powershell
# Copy your video into the media folder
copy "C:\path\to\your\marathi_video.mp4" "media\videos\"
```

Supported formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`

---

## Usage

### Index a video (Run once per video)

```powershell
python pipeline/index_video.py --video media/videos/your_video.mp4
```

Options:
```
--video           Path to video file (required)
--whisper-model   Override model: tiny/base/small/medium/large-v3
--force           Re-index even if already indexed
```

Example output:
```
╭─ Marathi RAG — Indexing Pipeline ─╮
│ Video: my_marathi_video.mp4        │
╰────────────────────────────────────╯
✓ Step 1/5 · Audio extracted → my_marathi_video.wav       [0:08]
✓ Step 2/5 · Transcription complete (342 segments)        [4:12]
✓ Step 3/5 · 48 chunks created                            [0:01]
✓ Step 4/5 · Embeddings generated (dim=1024)              [0:45]
✓ Step 5/5 · Stored in ChromaDB + SQLite                  [0:02]

┌──────────────────┬──────────────────────────────┐
│ Video ID         │ a3f2b1c0-...                 │
│ Video Name       │ my_marathi_video             │
│ Duration         │ 1843.2s (30.7 min)           │
│ Chunks Indexed   │ 48                           │
└──────────────────┴──────────────────────────────┘
```

### Start the backend

```powershell
uvicorn backend.main:app --reload
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Start the frontend

```powershell
cd frontend
npm run dev
```

Frontend runs at: http://localhost:3000

---

## API Reference

### `POST /api/v1/chat`
Ask a question about indexed videos.

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "शेतीबद्दल काय सांगितलं आहे?"}'
```

Response:
```json
{
  "answer": "...",
  "sources": [
    {
      "chunk_id": "uuid",
      "video_name": "my_video",
      "start_time": 120.5,
      "end_time": 145.2,
      "text": "...",
      "score": 0.89
    }
  ],
  "follow_up_questions": ["...", "...", "..."]
}
```

### `POST /api/v1/index`
Index a video (alternative to CLI script).

```bash
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{"video_path": "media/videos/sample.mp4"}'
```

### `GET /api/v1/videos`
List all indexed videos.

### `GET /api/v1/chunks?video_id=<uuid>`
List chunks for a specific video.

### `GET /health`
Health check.

---

## Project Structure

```
marathi-rag-prototype/
├── backend/
│   ├── main.py                      ← FastAPI app entry point
│   ├── config.py                    ← All settings from .env
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py              ← POST /chat
│   │   │   ├── index.py             ← POST /index
│   │   │   ├── videos.py            ← GET /videos
│   │   │   └── chunks.py            ← GET /chunks
│   │   └── schemas/
│   │       ├── chat.py              ← Pydantic request/response models
│   │       └── video.py
│   ├── services/
│   │   ├── asr/whisper_service.py   ← Whisper STT
│   │   ├── chunker/chunker_service.py ← Timestamp-aware chunker
│   │   ├── embedder/embedder_service.py ← bge-m3 embeddings
│   │   ├── retriever/retriever_service.py ← ChromaDB search
│   │   └── llm/groq_service.py     ← Groq API + prompt
│   ├── database/
│   │   ├── models.py                ← SQLAlchemy ORM models
│   │   ├── sqlite_client.py         ← SQLite connection
│   │   └── chroma_client.py         ← ChromaDB connection
│   └── utils/
│       ├── audio_extractor.py       ← FFmpeg wrapper
│       └── transcript_cleaner.py    ← Text normalization
│
├── pipeline/
│   └── index_video.py               ← CLI indexing script
│
├── frontend/
│   └── src/
│       ├── app/                     ← Next.js App Router pages
│       ├── components/              ← React components
│       ├── hooks/useChat.ts         ← Chat state hook
│       └── lib/api.ts               ← Typed API client
│
├── media/
│   ├── videos/                      ← DROP YOUR VIDEO HERE
│   ├── audio/                       ← Auto-generated WAV files
│   ├── transcripts/                 ← Raw Whisper JSON output
│   └── chunks/                      ← Chunk JSON files
│
├── database/
│   ├── chroma/                      ← ChromaDB vector data
│   └── sqlite/metadata.db           ← SQLite database
│
├── docs/migration_plan.md           ← Prototype → Production guide
├── .env.example                     ← Environment variable template
├── requirements.txt                 ← Python dependencies
└── README.md                        ← This file
```

---

## Troubleshooting

### FFmpeg not found
```
RuntimeError: FFmpeg failed
```
Solution: Ensure `ffmpeg` is in your system PATH. Restart terminal after installation.

### Whisper model download fails
Solution: Check internet connection. Models are downloaded to `~/.cache/whisper/`.

### bge-m3 download fails
Solution: Models download to `~/.cache/huggingface/`. Takes ~5 min on first run.

### ChromaDB version conflict
```
pip install "chromadb==0.5.15" --force-reinstall
```

### "No chunks found" error when chatting
You haven't indexed a video yet. Run the pipeline first:
```powershell
python pipeline/index_video.py --video media/videos/your_video.mp4
```

### Whisper is slow
- Use `--whisper-model small` or `--whisper-model base` for faster (less accurate) transcription
- Use `--whisper-model large-v3` with a GPU for best Marathi accuracy
- Add `EMBEDDING_DEVICE=cuda` to `.env` if you have a CUDA GPU

---

## Performance Expectations

| Whisper Model | Speed (CPU) | Marathi Quality | VRAM |
|---|---|---|---|
| tiny | Very fast | Poor | 1GB |
| base | Fast | Fair | 1GB |
| small | Moderate | Good | 2GB |
| **medium** | Slow | **Good (recommended for PoC)** | 5GB |
| large-v3 | Very slow on CPU | Best | 10GB |

For a 30-minute video on modern CPU:
- `medium` model: ~15-25 minutes transcription time
- `bge-m3` embeddings: ~5 minutes for ~50 chunks

---

## Testing

### Test the full pipeline end-to-end

```powershell
# 1. Index a video
python pipeline/index_video.py --video media/videos/test.mp4

# 2. Test the chat API directly
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "या व्हिडिओमध्ये काय सांगितले आहे?"}'

# 3. Check indexed videos
curl http://localhost:8000/api/v1/videos

# 4. Check chunks
curl "http://localhost:8000/api/v1/chunks?video_id=<your-video-id>"
```

### Validate chunk quality
```powershell
# View saved chunks JSON
type media\chunks\<video_id>_chunks.json
```

### Validate transcript
```powershell
# View raw Whisper transcript
type media\transcripts\<audio_name>_transcript.json
```

---

## Future: Scaling to Production

See [`docs/migration_plan.md`](docs/migration_plan.md) for the complete component swap guide.

| Now (Prototype) | Later (Production) | Effort |
|---|---|---|
| Local folder | Object Storage | Low |
| SQLite | PostgreSQL | Low (change 1 line) |
| ChromaDB | Qdrant | Low (swap 1 file) |
| CLI script | Celery workers | Medium |
| Whisper local | Whisper API | Low |
| No auth | OAuth2 | Medium |
| Single video | Thousands of videos | Low (infra only) |

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 14 + Tailwind CSS |
| ASR | OpenAI Whisper |
| Embeddings | BAAI/bge-m3 (sentence-transformers) |
| Vector DB | ChromaDB (local persistent) |
| Metadata DB | SQLite (SQLAlchemy ORM) |
| LLM | Groq API (llama-3.3-70b-versatile) |
| Audio | FFmpeg |
| Package Manager | pip / uv |

---

*Built as a production-mirrored local prototype for Marathi media RAG.*
