"""
backend/main.py

FastAPI application entry point.
Registers all routers, CORS middleware, and initializes the database on startup.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.sqlite_client import init_db
from backend.services.retriever.bm25_index import rebuild_index
from backend.api.routes import chat, index, videos, chunks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info("Starting Marathi RAG backend...")
    settings.ensure_dirs()   # Create all media/database directories
    init_db()                 # Create SQLite tables (idempotent)
    rebuild_index()           # Build BM25 index from existing chunks
    logger.info(f"Backend ready at http://{settings.backend_host}:{settings.backend_port}")
    yield
    logger.info("Backend shutting down.")


app = FastAPI(
    title="Marathi RAG Chatbot API",
    description="Local RAG prototype for Marathi media content — prototype for production architecture.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(index.router, prefix="/api/v1", tags=["Indexing"])
app.include_router(videos.router, prefix="/api/v1", tags=["Videos"])
app.include_router(chunks.router, prefix="/api/v1", tags=["Chunks"])


@app.get("/health", tags=["Health"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
