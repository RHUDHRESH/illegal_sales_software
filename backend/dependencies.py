"""Centralized dependency injection for FastAPI routes."""

from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session
from database import SessionLocal
from config import Settings


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only create one Settings instance.
    """
    return Settings()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection.
    Ensures proper session lifecycle management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
