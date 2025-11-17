"""Lead management - CRUD and scoring."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from dependencies import get_db
from schemas.lead import LeadResponse, LeadStatusUpdate, LeadNotesUpdate
from services.lead_service import LeadService

router = APIRouter()


@router.get("/", response_model=List[LeadResponse])
def list_leads(
    score_min: int = 0,
    score_max: int = 100,
    status: Optional[str] = None,
    score_bucket: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List leads with filtering."""
    return LeadService.list_leads(
        db=db,
        score_min=score_min,
        score_max=score_max,
        status=status,
        score_bucket=score_bucket,
        limit=limit,
        offset=offset,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead."""
    return LeadService.get_lead(db, lead_id)


@router.patch("/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update lead status."""
    lead = LeadService.update_lead_status(db, lead_id, status)
    return {
        "status": "ok",
        "lead_id": lead_id,
        "new_status": lead.status,
    }


@router.patch("/{lead_id}/notes")
def update_lead_notes(
    lead_id: int,
    notes: str,
    db: Session = Depends(get_db)
):
    """Update lead notes."""
    LeadService.update_lead_notes(db, lead_id, notes)
    return {"status": "ok"}


@router.get("/score-distribution/bucket-counts")
def get_bucket_counts(db: Session = Depends(get_db)):
    """Get count of leads by score bucket."""
    return LeadService.get_bucket_counts(db)


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead."""
    LeadService.delete_lead(db, lead_id)
    return {"message": "Lead deleted"}
