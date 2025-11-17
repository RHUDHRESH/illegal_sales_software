"""
Raptorflow Lead Engine - Main FastAPI App
Local Ollama-based lead discovery, classification, and enrichment.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import init_db, Base
from config import Settings
from routers import icp, leads, ingest, classify, scrape, advanced_scraping
from ollama_wrapper import OllamaManager
from scheduled_tasks import start_scheduler, stop_scheduler

# Load settings
settings = Settings()

# Initialize database
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Ollama manager
ollama_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global ollama_manager

    # Startup
    print("🚀 Initializing Raptorflow Lead Engine...")
    init_db(engine)

    # Initialize Ollama models
    print("📡 Checking Ollama models...")
    ollama_manager = OllamaManager()
    await ollama_manager.ensure_models_loaded()

    # Start scheduled tasks
    print("⏰ Starting scheduled tasks...")
    start_scheduler()

    print("✅ System ready!")
    yield

    # Shutdown
    print("🛑 Shutting down...")
    stop_scheduler()
    print("✅ Scheduler stopped")

# Create FastAPI app
app = FastAPI(
    title="Raptorflow Lead Engine",
    description="Overkill lead discovery + enrichment for marketing pain signals",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(icp.router, prefix="/api/icp", tags=["ICP Management"])
app.include_router(leads.router, prefix="/api/leads", tags=["Lead Management"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Data Ingest"])
app.include_router(classify.router, prefix="/api/classify", tags=["Classification"])
app.include_router(scrape.router, tags=["Web Scraping"])
app.include_router(advanced_scraping.router, prefix="/api/advanced", tags=["Advanced Scraping"])

@app.get("/")
def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "Raptorflow Lead Engine",
        "version": "0.1.0",
    }

@app.get("/health")
def health():
    """Full health check including Ollama status."""
    return {
        "api": "ok",
        "ollama": "checking...",
        "database": "ok",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
