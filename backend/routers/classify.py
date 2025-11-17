"""Classification logic - process signals through 1B + optional 4B."""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import logging

from dependencies import get_db, get_settings
from schemas.classification import SignalInput, ClassificationResult
from services.classification_service import ClassificationService
from config import Settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/signal", response_model=ClassificationResult)
async def classify_signal(
    signal: SignalInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Classify a signal (job post, website text, manual input, etc).
    1. Quick classification with Gemma 3 1B
    2. If score > threshold, queue 4B dossier generation
    3. Return lead with scores and classification
    """
    try:
        # Classify signal and create lead
        result = await ClassificationService.classify_signal(db, signal, settings)

        # If score > threshold, queue dossier generation
        if ClassificationService.should_generate_dossier(result.total_score, settings):
            lead_json = {
                "role_type": result.classification.get("role_type"),
                "company_name": signal.company_name,
                "pain_tags": result.classification.get("pain_tags", []),
                "situation": result.classification.get("situation", ""),
                "problem": result.classification.get("problem", ""),
            }
            signal_snippets = [signal.signal_text[:500]]  # Truncate for dossier

            # Queue background task
            background_tasks.add_task(
                ClassificationService.generate_dossier_async,
                result.lead_id,
                lead_json,
                signal_snippets,
                db,
            )
            logger.info(f"🔄 Queued dossier generation for lead {result.lead_id}")

        return result

    except Exception as e:
        logger.error(f"Error in classify_signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/batch")
async def classify_signals_batch(
    signals: list[SignalInput],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Classify multiple signals in sequence."""
    results = []
    for signal in signals:
        try:
            result = await ClassificationService.classify_signal(db, signal, settings)
            results.append({
                "signal": signal.signal_text[:100],
                "total_score": result.total_score,
                "status": "ok",
            })
        except Exception as e:
            results.append({
                "signal": signal.signal_text[:100],
                "error": str(e),
                "status": "error",
            })

    return {"count": len(results), "results": results}
