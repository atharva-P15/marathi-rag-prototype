"""
backend/config.py

Central configuration loaded from .env file.
All settings live here — never hardcoded elsewhere.
Production swap: Replace with environment-specific config loaders (e.g., AWS SSM, Vault).
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # --- Groq ---
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    groq_max_tokens: int = Field(default=2048, env="GROQ_MAX_TOKENS")
    groq_temperature: float = Field(default=0.1, env="GROQ_TEMPERATURE")

    # --- Whisper ---
    whisper_model: str = Field(default="medium", env="WHISPER_MODEL")

    # --- Embeddings ---
    embedding_model: str = Field(default="BAAI/bge-m3", env="EMBEDDING_MODEL")
    embedding_device: str = Field(default="cpu", env="EMBEDDING_DEVICE")

    # --- ChromaDB ---
    chroma_persist_dir: str = Field(default="./database/chroma", env="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="marathi_chunks", env="CHROMA_COLLECTION_NAME")

    # --- SQLite ---
    sqlite_db_path: str = Field(default="./database/sqlite/metadata.db", env="SQLITE_DB_PATH")

    # --- Media Paths ---
    media_videos_dir: str = Field(default="./media/videos", env="MEDIA_VIDEOS_DIR")
    media_audio_dir: str = Field(default="./media/audio", env="MEDIA_AUDIO_DIR")
    media_transcripts_dir: str = Field(default="./media/transcripts", env="MEDIA_TRANSCRIPTS_DIR")
    media_chunks_dir: str = Field(default="./media/chunks", env="MEDIA_CHUNKS_DIR")

    # --- Retrieval ---
    top_k_chunks: int = Field(default=5, env="TOP_K_CHUNKS")
    retrieval_candidates: int = Field(default=20, env="RETRIEVAL_CANDIDATES")
    enable_reranking: bool = Field(default=True, env="ENABLE_RERANKING")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", env="RERANKER_MODEL")
    enable_query_expansion: bool = Field(default=True, env="ENABLE_QUERY_EXPANSION")
    enable_contextual_compression: bool = Field(default=True, env="ENABLE_CONTEXTUAL_COMPRESSION")

    # --- Backend ---
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    cors_origins: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")

    # --- Chunking ---
    chunk_word_limit: int = Field(default=200, env="CHUNK_WORD_LIMIT")
    chunk_overlap_words: int = Field(default=40, env="CHUNK_OVERLAP_WORDS")
    chunk_min_words: int = Field(default=30, env="CHUNK_MIN_WORDS")
    # Legacy — kept for backward compat with .env files
    chunk_overlap_segments: int = Field(default=1, env="CHUNK_OVERLAP_SEGMENTS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    def ensure_dirs(self):
        """Create all required local directories if they don't exist."""
        dirs = [
            self.media_videos_dir,
            self.media_audio_dir,
            self.media_transcripts_dir,
            self.media_chunks_dir,
            self.chroma_persist_dir,
            str(Path(self.sqlite_db_path).parent),
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance — import this everywhere
settings = Settings()
