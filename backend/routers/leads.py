"""Lead management - CRUD and scoring."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import Lead, Company, Contact, Signal, SessionLocal
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class CompanySimple(BaseModel):
    id: int
    name: str
    website: Optional[str]
    sector: Optional[str]

    class Config:
        from_attributes = True

class ContactSimple(BaseModel):
    id: int
    name: Optional[str]
    role: Optional[str]
    email: Optional[str]
    phone_numbers: list

    class Config:
        from_attributes = True

class LeadResponse(BaseModel):
    id: int
    company_id: int
    contact_id: Optional[int]
    score_icp_fit: float
    score_marketing_pain: float
    score_data_quality: float
    total_score: float
    score_bucket: str
    role_type: Optional[str]
    pain_tags: list
    status: str
    created_at: datetime
    updated_at: datetime
    context_dossier: Optional[str]
    challenger_insight: Optional[str]
    reframe_suggestion: Optional[str]
    company: Optional[CompanySimple]
    contact: Optional[ContactSimple]

    class Config:
        from_attributes = True

class LeadFilter(BaseModel):
    score_min: int = 0
    score_max: int = 100
    status: Optional[str] = None
    score_bucket: Optional[str] = None
    limit: int = 50
    offset: int = 0

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
    query = db.query(Lead)

    # Apply filters
    if score_min:
        query = query.filter(Lead.total_score >= score_min)
    if score_max < 100:
        query = query.filter(Lead.total_score <= score_max)
    if status:
        query = query.filter(Lead.status == status)
    if score_bucket:
        query = query.filter(Lead.score_bucket == score_bucket)

    # Sort by score descending (hottest first)
    leads = query.order_by(Lead.total_score.desc()).offset(offset).limit(limit).all()
    return leads

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.patch("/{lead_id}/status")
def update_lead_status(lead_id: int, status: str, db: Session = Depends(get_db)):
    """Update lead status."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    valid_statuses = ["new", "contacted", "qualified", "pitched", "trial", "won", "lost", "parked"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    lead.status = status
    lead.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "ok", "lead_id": lead_id, "new_status": status}

@router.patch("/{lead_id}/notes")
def update_lead_notes(lead_id: int, notes: str, db: Session = Depends(get_db)):
    """Update lead notes."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.notes = notes
    lead.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@router.get("/score-distribution/bucket-counts")
def get_bucket_counts(db: Session = Depends(get_db)):
    """Get count of leads by score bucket."""
    from sqlalchemy import func

    counts = db.query(
        Lead.score_bucket,
        func.count(Lead.id).label("count")
    ).group_by(Lead.score_bucket).all()

    return {
        "red_hot": next((c[1] for c in counts if c[0] == "red_hot"), 0),
        "warm": next((c[1] for c in counts if c[0] == "warm"), 0),
        "nurture": next((c[1] for c in counts if c[0] == "nurture"), 0),
        "parked": next((c[1] for c in counts if c[0] == "parked"), 0),
    }

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted"}
