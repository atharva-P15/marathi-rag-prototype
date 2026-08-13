"""
backend/database/sqlite_client.py

SQLite session management using SQLAlchemy.
Production swap: Replace SQLITE_URL with a PostgreSQL connection string.
All query logic stays the same because SQLAlchemy abstracts the driver.
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.database.models import Base
from backend.config import settings


def _get_engine():
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path.resolve()}"
    return create_engine(url, connect_args={"check_same_thread": False})


_engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def init_db():
    """Create all tables. Safe to call on every startup (idempotent)."""
    Base.metadata.create_all(bind=_engine)


def get_db() -> Session:
    """
    FastAPI dependency injection: yields a database session per request.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
