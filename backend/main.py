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
from ollama_wrapper import init_ollama_manager, get_ollama_manager
from cache_manager import init_cache_manager, get_cache_manager
from prompt_templates import init_prompt_manager, get_prompt_manager
from scoring_heuristics import init_scoring_heuristics, get_scoring_heuristics
from scheduled_tasks import start_scheduler, stop_scheduler

# Load settings
settings = Settings()

# Initialize database
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic with enhanced AI infrastructure initialization."""
    # Startup
    print("🚀 Initializing Raptorflow Lead Engine...")
    init_db(engine)

    # Initialize cache manager
    print("💾 Initializing cache manager...")
    cache_manager = init_cache_manager(
        backend=settings.cache_backend,
        redis_url=settings.redis_url if settings.cache_backend == "redis" else None,
        max_size=settings.cache_max_size,
        ttl_seconds=settings.cache_ttl_seconds
    )
    if settings.cache_backend == "redis":
        await cache_manager.connect_redis()
    print(f"✅ Cache initialized: backend={settings.cache_backend}, enabled={settings.enable_response_cache}")

    # Initialize prompt template manager
    print("📝 Initializing prompt template manager...")
    prompt_manager = init_prompt_manager(
        template_path=settings.prompt_template_path,
        enable_custom=settings.enable_custom_prompts
    )
    print(f"✅ Prompt manager initialized: templates={len(prompt_manager.list_templates())}")

    # Initialize Ollama manager (singleton)
    print("📡 Initializing Ollama manager...")
    ollama_manager = init_ollama_manager()
    await ollama_manager.ensure_models_loaded()
    print(f"✅ Ollama ready: 1B={ollama_manager.model_1b}, 4B={ollama_manager.model_4b}")

    # Initialize scoring heuristics
    print("🎯 Initializing scoring heuristics...")
    scoring_heuristics = init_scoring_heuristics(
        scoring_weights={
            "icp_fit": settings.scoring_weight_icp_fit,
            "marketing_pain": settings.scoring_weight_marketing_pain,
            "data_quality": settings.scoring_weight_data_quality
        }
    )
    print(f"✅ Scoring heuristics initialized (weights: fit={settings.scoring_weight_icp_fit}, pain={settings.scoring_weight_marketing_pain}, quality={settings.scoring_weight_data_quality})")

    # Start scheduled tasks
    print("⏰ Starting scheduled tasks...")
    start_scheduler()

    print("\n" + "="*60)
    print("✅ Raptorflow Lead Engine READY!")
    print("="*60)
    print(f"  📊 Cache: {settings.cache_backend} (enabled={settings.enable_response_cache})")
    print(f"  🤖 Models: {ollama_manager.model_1b} + {ollama_manager.model_4b}")
    print(f"  📝 Prompts: {len(prompt_manager.list_templates())} templates")
    print(f"  ⚡ Health Monitoring: {settings.enable_health_monitoring}")
    print(f"  🔄 Batch Parallel: {settings.batch_enable_parallel} (max={settings.batch_concurrency_limit})")
    print(f"  🎯 Scoring Heuristics: {settings.enable_scoring_heuristics}")
    print(f"  🅿️  Auto-park: {settings.enable_auto_park} (after {settings.auto_park_days} days)")
    print("="*60 + "\n")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    stop_scheduler()
    print("✅ Scheduler stopped")

    # Disconnect Redis if used
    if settings.cache_backend == "redis":
        cache_mgr = get_cache_manager()
        if cache_mgr:
            await cache_mgr.disconnect_redis()
            print("✅ Redis disconnected")

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
async def health():
    """Full health check including Ollama, cache, and AI infrastructure status."""
    ollama = get_ollama_manager()
    cache = get_cache_manager()
    prompt_mgr = get_prompt_manager()

    health_data = {
        "api": "ok",
        "database": "ok",
        "ollama": {
            "status": "ok" if ollama else "not_initialized",
            "models": {
                "1b": ollama.model_1b if ollama else None,
                "4b": ollama.model_4b if ollama else None,
            },
            "health_monitoring": settings.enable_health_monitoring
        },
        "cache": {
            "status": "ok" if cache else "not_initialized",
            "backend": settings.cache_backend,
            "enabled": settings.enable_response_cache
        },
        "prompts": {
            "status": "ok" if prompt_mgr else "not_initialized",
            "custom_enabled": settings.enable_custom_prompts,
            "template_count": len(prompt_mgr.list_templates()) if prompt_mgr else 0
        },
        "features": {
            "embeddings": settings.enable_embeddings,
            "streaming": settings.enable_streaming,
            "batch_parallel": settings.batch_enable_parallel,
            "health_monitoring": settings.enable_health_monitoring
        }
    }

    # Add detailed health stats if monitoring enabled
    if ollama and settings.enable_health_monitoring and ollama.health_monitor:
        health_data["ollama"]["health_stats"] = ollama.health_monitor.get_stats()

    return health_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
