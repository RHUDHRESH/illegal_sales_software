"""Configuration for the Raptorflow Lead Engine."""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """App settings loaded from env vars."""

    # API
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./raptorflow_leads.db")

    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model_1b: str = os.getenv("OLLAMA_MODEL_1B", "gemma3:1b")
    ollama_model_4b: str = os.getenv("OLLAMA_MODEL_4B", "gemma3:4b")

    # Classifiers
    classifier_score_threshold: int = 70  # Only generate 4B dossier for leads > this score

    class Config:
        env_file = ".env"
        case_sensitive = False
