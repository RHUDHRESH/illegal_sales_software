"""ICP Whiteboard - define and manage Ideal Customer Profiles."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import ICPProfile, SessionLocal
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
class ICPCreate(BaseModel):
    name: str
    description: str = None
    size_buckets: List[str] = []
    industries: List[str] = []
    locations: List[str] = []
    stages: List[str] = []
    hiring_keywords: List[str] = []
    pain_keywords: List[str] = []
    channel_preferences: List[str] = []
    budget_signals: List[str] = []

class ICPUpdate(BaseModel):
    name: str = None
    description: str = None
    size_buckets: List[str] = None
    industries: List[str] = None
    locations: List[str] = None
    stages: List[str] = None
    hiring_keywords: List[str] = None
    pain_keywords: List[str] = None
    channel_preferences: List[str] = None
    budget_signals: List[str] = None

class ICPResponse(BaseModel):
    id: int
    name: str
    description: str = None
    size_buckets: List[str]
    industries: List[str]
    locations: List[str]
    stages: List[str]
    hiring_keywords: List[str]
    pain_keywords: List[str]
    channel_preferences: List[str]
    budget_signals: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ICPResponse)
def create_icp(icp: ICPCreate, db: Session = Depends(get_db)):
    """Create a new ICP profile."""
    # Check if name already exists
    existing = db.query(ICPProfile).filter(ICPProfile.name == icp.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="ICP profile with this name already exists")

    db_icp = ICPProfile(
        name=icp.name,
        description=icp.description,
        size_buckets=icp.size_buckets,
        industries=icp.industries,
        locations=icp.locations,
        stages=icp.stages,
        hiring_keywords=icp.hiring_keywords,
        pain_keywords=icp.pain_keywords,
        channel_preferences=icp.channel_preferences,
        budget_signals=icp.budget_signals,
    )
    db.add(db_icp)
    db.commit()
    db.refresh(db_icp)
    return db_icp

@router.get("/", response_model=List[ICPResponse])
def list_icps(db: Session = Depends(get_db)):
    """List all ICP profiles."""
    icps = db.query(ICPProfile).all()
    return icps

@router.get("/{icp_id}", response_model=ICPResponse)
def get_icp(icp_id: int, db: Session = Depends(get_db)):
    """Get a specific ICP profile."""
    icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
    if not icp:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return icp

@router.put("/{icp_id}", response_model=ICPResponse)
def update_icp(icp_id: int, icp_update: ICPUpdate, db: Session = Depends(get_db)):
    """Update an ICP profile."""
    icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
    if not icp:
        raise HTTPException(status_code=404, detail="ICP profile not found")

    # Update fields if provided
    update_data = icp_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(icp, key, value)

    icp.updated_at = datetime.utcnow()
    db.add(icp)
    db.commit()
    db.refresh(icp)
    return icp

@router.delete("/{icp_id}")
def delete_icp(icp_id: int, db: Session = Depends(get_db)):
    """Delete an ICP profile."""
    icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
    if not icp:
        raise HTTPException(status_code=404, detail="ICP profile not found")

    db.delete(icp)
    db.commit()
    return {"message": "ICP profile deleted"}

# Sample ICP templates
@router.post("/templates/solo-founder")
def create_solo_founder_icp(db: Session = Depends(get_db)):
    """Create a pre-built ICP for solo founders."""
    icp = ICPCreate(
        name="Solo Founder - Service Business",
        description="Solo founder or 1-person team running a service business, looking to scale marketing",
        size_buckets=["1"],
        industries=["consulting", "freelance", "agency", "coaching"],
        locations=["india"],
        stages=["freelancer", "solo-founder"],
        hiring_keywords=["marketing manager", "growth hacker", "performance marketer", "first marketing hire"],
        pain_keywords=["lead generation", "scaling", "no marketing team", "need help marketing"],
        channel_preferences=["linkedin", "instagram", "email"],
        budget_signals=["diy", "first hire"],
    )
    return create_icp(icp, db)

@router.post("/templates/small-d2c")
def create_small_d2c_icp(db: Session = Depends(get_db)):
    """Create a pre-built ICP for small D2C brands."""
    icp = ICPCreate(
        name="Small D2C Brand",
        description="Small D2C/eCommerce brand <10 people, running ads but no cohesive strategy",
        size_buckets=["2-5", "6-10"],
        industries=["ecommerce", "d2c", "saas", "consumer"],
        locations=["india"],
        stages=["early-startup", "small-agency"],
        hiring_keywords=["marketing", "growth", "brand manager", "performance"],
        pain_keywords=["roas", "cac", "retention", "brand building", "lead quality"],
        channel_preferences=["instagram", "facebook", "google", "tiktok"],
        budget_signals=["1-junior-marketer", "agency unhappy"],
    )
    return create_icp(icp, db)
