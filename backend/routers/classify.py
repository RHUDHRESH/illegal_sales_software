"""Enhanced classification logic with concurrent processing, caching, embeddings, and advanced scoring heuristics."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from database import Lead, Company, Contact, Signal, ICPProfile, SessionLocal, FundingEvent, ScoreOverride, ContentActivity
from pydantic import BaseModel
from datetime import datetime, timedelta
from config import Settings
from ollama_wrapper import get_ollama_manager
from cache_manager import get_cache_manager
from prompt_templates import get_prompt_manager
from scoring_heuristics import get_scoring_heuristics

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
    post_date: Optional[datetime] = None  # When signal was posted
    industry: Optional[str] = None  # Industry classification

class ClassificationResult(BaseModel):
    icp_match: bool
    total_score: float
    score_bucket: str
    classification: Dict[str, Any]
    company_id: Optional[int]
    lead_id: Optional[int]
    heuristic_adjustments: Optional[List[Dict[str, Any]]] = []
    score_explanation: Optional[Dict[str, Any]] = None

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

        # Base scores
        base_score_fit = classification.get("score_fit", 0)
        base_score_pain = classification.get("score_pain", 0)
        base_score_quality = classification.get("score_data_quality", 0)

        # Apply scoring heuristics if enabled
        heuristic_adjustments = []
        total_adjustment = 0
        score_explanation = None

        if settings.enable_scoring_heuristics:
            scoring_heuristics = get_scoring_heuristics()
            if scoring_heuristics:
                # Apply heuristics
                total_adjustment, adjustments = scoring_heuristics.apply_all_heuristics(
                    signal_text=signal.signal_text,
                    post_date=signal.post_date,
                    company_name=signal.company_name,
                    source_url=signal.source_url,
                    industry=signal.industry
                )
                heuristic_adjustments = [
                    {
                        "category": adj.category,
                        "adjustment": adj.adjustment,
                        "reason": adj.reason,
                        "confidence": adj.confidence
                    }
                    for adj in adjustments
                ]

                # Generate score explanation
                score_explanation = scoring_heuristics.explain_score(
                    base_scores={
                        "score_fit": base_score_fit,
                        "score_pain": base_score_pain,
                        "score_data_quality": base_score_quality
                    },
                    adjustments=adjustments
                )

        # Compute final score
        base_total = base_score_fit + base_score_pain + base_score_quality
        total_score = base_total + total_adjustment

        # Check for funding boost
        if signal.company_name:
            recent_funding = db.query(FundingEvent).filter(
                FundingEvent.company_id.isnot(None),
                FundingEvent.announced_date >= datetime.utcnow() - timedelta(days=settings.funding_boost_days)
            ).first()
            if recent_funding:
                funding_bonus = settings.funding_boost_score
                total_score += funding_bonus
                heuristic_adjustments.append({
                    "category": "funding_event",
                    "adjustment": funding_bonus,
                    "reason": f"Recent funding event within {settings.funding_boost_days} days",
                    "confidence": 0.9
                })
                logger.info(f"Funding boost applied: +{funding_bonus} (company: {signal.company_name})")

        # Clamp score to 0-100
        total_score = max(0, min(100, total_score))
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

        # Extract heuristic scores from adjustments
        ghost_job_score = next((adj["adjustment"] for adj in heuristic_adjustments if adj["category"] == "ghost_job"), 0)
        first_marketer_bonus = next((adj["adjustment"] for adj in heuristic_adjustments if adj["category"] == "first_marketer"), 0)
        founder_tone_score = next((adj["adjustment"] for adj in heuristic_adjustments if adj["category"] == "tone_classification"), 0)
        industry_bonus = next((adj["adjustment"] for adj in heuristic_adjustments if adj["category"] == "industry_specific"), 0)
        spam_penalty = next((adj["adjustment"] for adj in heuristic_adjustments if adj["category"] == "spam_detection"), 0)

        # Create lead with heuristics metadata
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
            heuristic_adjustments=heuristic_adjustments,
            ghost_job_score=ghost_job_score,
            first_marketer_bonus=first_marketer_bonus,
            founder_tone_score=founder_tone_score,
            industry_bonus=industry_bonus,
            spam_penalty=spam_penalty,
            signal_post_date=signal.post_date,
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
            heuristic_adjustments=heuristic_adjustments,
            score_explanation=score_explanation,
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


# Funding Events Management

class FundingEventInput(BaseModel):
    company_name: str
    event_type: str  # "seed", "series_a", "series_b", etc.
    amount_usd: Optional[float] = None
    announced_date: datetime
    source: Optional[str] = "manual"
    notes: Optional[str] = None


@router.post("/funding-events")
async def create_funding_event(
    event: FundingEventInput,
    db: Session = Depends(get_db)
):
    """
    Add a funding event for a company.

    This will boost leads for this company if posted within the funding_boost_days window.
    """
    # Find company
    company = db.query(Company).filter(
        Company.name.ilike(event.company_name)
    ).first()

    if not company:
        # Create company if doesn't exist
        company = Company(name=event.company_name, country="india")
        db.add(company)
        db.commit()
        db.refresh(company)

    # Create funding event
    db_event = FundingEvent(
        company_id=company.id,
        event_type=event.event_type,
        amount_usd=event.amount_usd,
        announced_date=event.announced_date,
        source=event.source,
        notes=event.notes
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    logger.info(f"✅ Funding event created: {company.name} - {event.event_type}")

    return {
        "id": db_event.id,
        "company_id": company.id,
        "company_name": company.name,
        "event_type": event.event_type,
        "announced_date": event.announced_date
    }


@router.get("/funding-events")
async def list_funding_events(
    days: int = 90,
    db: Session = Depends(get_db)
):
    """List recent funding events."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    events = db.query(FundingEvent).filter(
        FundingEvent.announced_date >= cutoff_date
    ).order_by(FundingEvent.announced_date.desc()).all()

    return {
        "count": len(events),
        "events": [
            {
                "id": event.id,
                "company_id": event.company_id,
                "event_type": event.event_type,
                "amount_usd": event.amount_usd,
                "announced_date": event.announced_date,
                "source": event.source,
                "notes": event.notes
            }
            for event in events
        ]
    }


# Manual Score Overrides

class ScoreOverrideInput(BaseModel):
    override_score: float
    reason: Optional[str] = None
    user: str = "admin"


@router.post("/leads/{lead_id}/override-score")
async def override_lead_score(
    lead_id: int,
    override: ScoreOverrideInput,
    db: Session = Depends(get_db)
):
    """
    Manually override a lead's score.

    The override is stored separately and applied on top of the calculated score.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Store override
    original_score = lead.total_score

    db_override = ScoreOverride(
        lead_id=lead_id,
        user=override.user,
        original_score=original_score,
        override_score=override.override_score,
        reason=override.reason
    )
    db.add(db_override)

    # Update lead
    lead.manual_score_override = override.override_score
    lead.override_reason = override.reason
    lead.total_score = override.override_score
    lead.score_bucket = compute_score_bucket(override.override_score)
    lead.updated_at = datetime.utcnow()

    db.commit()

    logger.info(f"✅ Score override applied to lead {lead_id}: {original_score} → {override.override_score}")

    return {
        "lead_id": lead_id,
        "original_score": original_score,
        "override_score": override.override_score,
        "new_bucket": lead.score_bucket,
        "reason": override.reason
    }


@router.get("/leads/{lead_id}/score-history")
async def get_score_history(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get score override history for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    overrides = db.query(ScoreOverride).filter(
        ScoreOverride.lead_id == lead_id
    ).order_by(ScoreOverride.timestamp.desc()).all()

    return {
        "lead_id": lead_id,
        "current_score": lead.total_score,
        "manual_override": lead.manual_score_override,
        "override_count": len(overrides),
        "history": [
            {
                "id": override.id,
                "user": override.user,
                "original_score": override.original_score,
                "override_score": override.override_score,
                "reason": override.reason,
                "timestamp": override.timestamp
            }
            for override in overrides
        ]
    }


# Auto-park leads

@router.post("/leads/auto-park")
async def auto_park_old_leads(
    dry_run: bool = False,
    db: Session = Depends(get_db)
):
    """
    Automatically park leads that haven't been contacted in auto_park_days.

    Args:
        dry_run: If true, just return what would be parked without changing anything
    """
    settings = Settings()

    if not settings.enable_auto_park:
        return {"message": "Auto-park is disabled in configuration"}

    cutoff_date = datetime.utcnow() - timedelta(days=settings.auto_park_days)

    # Find leads to park:
    # - Status is "new" (not contacted)
    # - Created more than auto_park_days ago
    # - Not already parked
    leads_to_park = db.query(Lead).filter(
        Lead.status == "new",
        Lead.created_at < cutoff_date,
        Lead.auto_parked_at.is_(None)
    ).all()

    if dry_run:
        return {
            "dry_run": True,
            "leads_to_park": len(leads_to_park),
            "leads": [
                {
                    "id": lead.id,
                    "company_id": lead.company_id,
                    "total_score": lead.total_score,
                    "created_at": lead.created_at,
                    "days_old": (datetime.utcnow() - lead.created_at).days
                }
                for lead in leads_to_park
            ]
        }

    # Actually park the leads
    parked_count = 0
    for lead in leads_to_park:
        lead.status = "parked"
        lead.auto_parked_at = datetime.utcnow()
        lead.notes = (lead.notes or "") + f"\n[Auto-parked on {datetime.utcnow().date()} - no contact for {settings.auto_park_days} days]"
        db.add(lead)
        parked_count += 1

    db.commit()

    logger.info(f"✅ Auto-parked {parked_count} leads older than {settings.auto_park_days} days")

    return {
        "parked_count": parked_count,
        "cutoff_date": cutoff_date,
        "auto_park_days": settings.auto_park_days
    }
