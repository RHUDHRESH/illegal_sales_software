"""Classification logic - process signals through 1B + optional 4B."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import asyncio
import json
import logging
from database import Lead, Company, Contact, Signal, ICPProfile, SessionLocal
from pydantic import BaseModel
from datetime import datetime
from config import Settings
from ollama_wrapper import OllamaManager

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
        ollama = OllamaManager()
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

        # Initialize Ollama manager
        ollama = OllamaManager()

        # 1B classification
        classification = await ollama.classify_signal(signal.signal_text, icp_context)

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
    signals: list[SignalInput],
    db: Session = Depends(get_db),
):
    """Classify multiple signals in sequence."""
    results = []
    for signal in signals:
        try:
            # Note: in production, you'd want to chunk these differently
            # For now, process sequentially
            ollama = OllamaManager()
            classification = await ollama.classify_signal(signal.signal_text)

            total_score = (
                classification.get("score_fit", 0) +
                classification.get("score_pain", 0) +
                classification.get("score_data_quality", 0)
            )

            results.append({
                "signal": signal.signal_text[:100],
                "total_score": total_score,
                "status": "ok",
            })
        except Exception as e:
            results.append({
                "signal": signal.signal_text[:100],
                "error": str(e),
                "status": "error",
            })

    return {"count": len(results), "results": results}
