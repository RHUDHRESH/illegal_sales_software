"""Enhanced classification logic with concurrent processing, caching, and embeddings."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from database import Lead, Company, Contact, Signal, ICPProfile, SessionLocal
from pydantic import BaseModel
from datetime import datetime
from config import Settings
from ollama_wrapper import get_ollama_manager
from cache_manager import get_cache_manager
from prompt_templates import get_prompt_manager

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SignalInput(BaseModel):
    signal_text: str
    source_type: str = "manual"
    source_url: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None

class ClassificationResult(BaseModel):
    icp_match: bool
    total_score: float
    score_bucket: str
    classification: Dict[str, Any]
    company_id: Optional[int]
    lead_id: Optional[int]

def compute_score_bucket(total_score: float) -> str:
    """Convert score to bucket."""
    if total_score >= 80:
        return "red_hot"
    elif total_score >= 60:
        return "warm"
    elif total_score >= 40:
        return "nurture"
    else:
        return "parked"

async def generate_dossier_async(
    lead_id: int,
    lead_json: Dict[str, Any],
    signal_snippets: list,
    db: Session,
):
    """Background task to generate 4B dossier for high-scoring leads."""
    try:
        ollama = get_ollama_manager()
        if not ollama:
            logger.error("OllamaManager not initialized")
            return

        dossier = await ollama.generate_dossier(lead_json, signal_snippets)

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.context_dossier = dossier.get("snapshot", "") + "\n\n" + \
                                  "\n".join(dossier.get("why_pain_bullets", []))
            lead.challenger_insight = dossier.get("challenger_insight", "")
            lead.reframe_suggestion = dossier.get("reframe_suggestion", "")
            lead.updated_at = datetime.utcnow()
            db.add(lead)
            db.commit()
            logger.info(f"✅ Dossier generated for lead {lead_id}")
    except Exception as e:
        logger.error(f"Error generating dossier for lead {lead_id}: {e}")

@router.post("/signal", response_model=ClassificationResult)
async def classify_signal(
    signal: SignalInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Classify a signal (job post, website text, manual input, etc).
    1. Quick classification with Gemma 3 1B
    2. If score > threshold, queue 4B dossier generation
    3. Return lead with scores and classification
    """
    try:
        # Get list of ICPs to pass context
        icps = db.query(ICPProfile).all()
        icp_context = {
            "size_buckets": ["1", "2-5", "6-10", "11-20"],
            "industries": list(set([ind for icp in icps for ind in icp.industries])),
            "pain_keywords": list(set([kw for icp in icps for kw in icp.pain_keywords])),
            "hiring_keywords": list(set([kw for icp in icps for kw in icp.hiring_keywords])),
        }

        # Get singleton Ollama manager
        ollama = get_ollama_manager()
        if not ollama:
            raise HTTPException(status_code=500, detail="OllamaManager not initialized")

        # 1B classification (with caching)
        classification = await ollama.classify_signal(signal.signal_text, icp_context, use_cache=True)

        # Compute total score
        total_score = (
            classification.get("score_fit", 0) +
            classification.get("score_pain", 0) +
            classification.get("score_data_quality", 0)
        )
        score_bucket = compute_score_bucket(total_score)

        # Get or create company
        company_id = None
        if signal.company_name:
            company = db.query(Company).filter(
                (Company.name.ilike(signal.company_name)) |
                (Company.website == signal.company_website)
            ).first()

            if not company:
                company = Company(
                    name=signal.company_name,
                    website=signal.company_website,
                    country="india",
                )
                db.add(company)
                db.commit()
                db.refresh(company)

            company_id = company.id

        # Create signal record
        db_signal = Signal(
            company_id=company_id,
            source_type=signal.source_type,
            source_url=signal.source_url,
            raw_text=signal.signal_text,
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)

        # Create lead
        db_lead = Lead(
            company_id=company_id,
            score_icp_fit=classification.get("score_fit", 0),
            score_marketing_pain=classification.get("score_pain", 0),
            score_data_quality=classification.get("score_data_quality", 0),
            total_score=total_score,
            score_bucket=score_bucket,
            role_type=classification.get("role_type", "unclear"),
            pain_tags=classification.get("pain_tags", []),
            situation=classification.get("situation", ""),
            problem=classification.get("problem", ""),
            implication=classification.get("implication", ""),
            need_payoff=classification.get("need_payoff", ""),
            economic_buyer_guess=classification.get("economic_buyer_guess", ""),
            key_pain=classification.get("key_pain", ""),
            chaos_flags=classification.get("chaos_flags", []),
            silver_bullet_phrases=classification.get("silver_bullet_phrases", []),
            status="new",
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)

        logger.info(f"✅ Lead {db_lead.id} created with score {total_score}")

        # If score > threshold, queue dossier generation
        settings = Settings()
        if total_score > settings.classifier_score_threshold:
            lead_json = {
                "role_type": classification.get("role_type"),
                "company_name": signal.company_name,
                "pain_tags": classification.get("pain_tags", []),
                "situation": classification.get("situation", ""),
                "problem": classification.get("problem", ""),
            }
            signal_snippets = [signal.signal_text[:500]]  # Truncate for dossier

            # Queue background task
            background_tasks.add_task(
                generate_dossier_async,
                db_lead.id,
                lead_json,
                signal_snippets,
                db,
            )
            logger.info(f"🔄 Queued dossier generation for lead {db_lead.id}")

        return ClassificationResult(
            icp_match=classification.get("icp_match", False),
            total_score=total_score,
            score_bucket=score_bucket,
            classification=classification,
            company_id=company_id,
            lead_id=db_lead.id,
        )

    except Exception as e:
        logger.error(f"Error in classify_signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signal/batch")
async def classify_signals_batch(
    signals: List[SignalInput],
    db: Session = Depends(get_db),
):
    """
    Classify multiple signals in parallel using asyncio.gather.

    Features:
    - Concurrent processing with configurable concurrency limit
    - Multi-stage filtering (prefilter with score threshold)
    - Caching for repeated signals
    - Batch creation of leads
    """
    settings = Settings()
    ollama = get_ollama_manager()
    if not ollama:
        raise HTTPException(status_code=500, detail="OllamaManager not initialized")

    # Get ICP context once
    icps = db.query(ICPProfile).all()
    icp_context = {
        "size_buckets": ["1", "2-5", "6-10", "11-20"],
        "industries": list(set([ind for icp in icps for ind in icp.industries])),
        "pain_keywords": list(set([kw for icp in icps for kw in icp.pain_keywords])),
        "hiring_keywords": list(set([kw for icp in icps for kw in icp.hiring_keywords])),
    }

    async def classify_single(signal: SignalInput) -> Dict[str, Any]:
        """Classify a single signal with error handling."""
        try:
            classification = await ollama.classify_signal(
                signal.signal_text,
                icp_context,
                use_cache=True
            )

            total_score = (
                classification.get("score_fit", 0) +
                classification.get("score_pain", 0) +
                classification.get("score_data_quality", 0)
            )

            # Multi-stage filtering: skip low-scoring signals
            if total_score < settings.prefilter_score_threshold:
                logger.debug(f"Signal filtered out (score={total_score} < {settings.prefilter_score_threshold})")
                return {
                    "signal": signal.signal_text[:100],
                    "total_score": total_score,
                    "status": "filtered",
                    "classification": classification
                }

            return {
                "signal": signal.signal_text[:100],
                "total_score": total_score,
                "status": "ok",
                "classification": classification,
                "signal_obj": signal
            }

        except Exception as e:
            logger.error(f"Error classifying signal: {e}")
            return {
                "signal": signal.signal_text[:100],
                "error": str(e),
                "status": "error",
            }

    # Process signals concurrently with semaphore for rate limiting
    if settings.batch_enable_parallel:
        semaphore = asyncio.Semaphore(settings.batch_concurrency_limit)

        async def classify_with_semaphore(signal: SignalInput):
            async with semaphore:
                return await classify_single(signal)

        logger.info(f"Processing {len(signals)} signals in parallel (concurrency={settings.batch_concurrency_limit})")
        results = await asyncio.gather(*[classify_with_semaphore(s) for s in signals])
    else:
        logger.info(f"Processing {len(signals)} signals sequentially")
        results = []
        for signal in signals:
            result = await classify_single(signal)
            results.append(result)

    # Create leads for successful classifications
    created_leads = []
    for result in results:
        if result["status"] == "ok" and "classification" in result:
            try:
                classification = result["classification"]
                signal_obj = result["signal_obj"]
                total_score = result["total_score"]
                score_bucket = compute_score_bucket(total_score)

                # Get or create company
                company_id = None
                if signal_obj.company_name:
                    company = db.query(Company).filter(
                        (Company.name.ilike(signal_obj.company_name)) |
                        (Company.website == signal_obj.company_website)
                    ).first()

                    if not company:
                        company = Company(
                            name=signal_obj.company_name,
                            website=signal_obj.company_website,
                            country="india",
                        )
                        db.add(company)
                        db.commit()
                        db.refresh(company)

                    company_id = company.id

                # Create signal record
                db_signal = Signal(
                    company_id=company_id,
                    source_type=signal_obj.source_type,
                    source_url=signal_obj.source_url,
                    raw_text=signal_obj.signal_text,
                )
                db.add(db_signal)
                db.commit()
                db.refresh(db_signal)

                # Create lead
                db_lead = Lead(
                    company_id=company_id,
                    score_icp_fit=classification.get("score_fit", 0),
                    score_marketing_pain=classification.get("score_pain", 0),
                    score_data_quality=classification.get("score_data_quality", 0),
                    total_score=total_score,
                    score_bucket=score_bucket,
                    role_type=classification.get("role_type", "unclear"),
                    pain_tags=classification.get("pain_tags", []),
                    situation=classification.get("situation", ""),
                    problem=classification.get("problem", ""),
                    implication=classification.get("implication", ""),
                    need_payoff=classification.get("need_payoff", ""),
                    economic_buyer_guess=classification.get("economic_buyer_guess", ""),
                    key_pain=classification.get("key_pain", ""),
                    chaos_flags=classification.get("chaos_flags", []),
                    silver_bullet_phrases=classification.get("silver_bullet_phrases", []),
                    status="new",
                )
                db.add(db_lead)
                db.commit()
                db.refresh(db_lead)

                created_leads.append(db_lead.id)
                result["lead_id"] = db_lead.id

                logger.info(f"✅ Lead {db_lead.id} created (batch) with score {total_score}")

            except Exception as e:
                logger.error(f"Error creating lead from batch result: {e}")
                result["status"] = "error"
                result["error"] = str(e)

    # Clean up results (remove signal_obj which is not JSON serializable)
    for result in results:
        result.pop("signal_obj", None)

    return {
        "count": len(results),
        "created_leads": len(created_leads),
        "filtered": sum(1 for r in results if r.get("status") == "filtered"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "results": results
    }


@router.get("/metrics")
async def get_classification_metrics():
    """
    Get AI model and cache metrics.

    Returns stats on:
    - Model usage (classification, dossier, embedding counts)
    - Cache performance (hit rate, size)
    - Health monitoring (Ollama availability, latency)
    """
    ollama = get_ollama_manager()
    cache = get_cache_manager()

    metrics = {}

    if ollama:
        metrics["ollama"] = ollama.get_stats()
    else:
        metrics["ollama"] = {"error": "OllamaManager not initialized"}

    if cache:
        metrics["cache"] = cache.get_stats()
    else:
        metrics["cache"] = {"enabled": False}

    return metrics


@router.post("/cache/clear")
async def clear_classification_cache():
    """Clear the classification cache (admin endpoint)."""
    cache = get_cache_manager()
    if not cache:
        raise HTTPException(status_code=500, detail="Cache not initialized")

    await cache.clear_all()
    return {"status": "ok", "message": "Cache cleared successfully"}


@router.post("/templates/reload")
async def reload_prompt_templates():
    """Reload prompt templates from disk (admin endpoint)."""
    prompt_manager = get_prompt_manager()
    if not prompt_manager:
        raise HTTPException(status_code=500, detail="Prompt manager not initialized")

    prompt_manager.reload_templates()
    return {
        "status": "ok",
        "message": "Templates reloaded successfully",
        "templates": prompt_manager.list_templates()
    }
