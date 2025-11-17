"""ICP Whiteboard - define and manage Ideal Customer Profiles."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db
from schemas.icp import ICPCreate, ICPUpdate, ICPResponse
from services.icp_service import ICPService

router = APIRouter()


@router.post("/", response_model=ICPResponse)
def create_icp(icp: ICPCreate, db: Session = Depends(get_db)):
    """Create a new ICP profile."""
    return ICPService.create_icp(db, icp)


@router.get("/", response_model=List[ICPResponse])
def list_icps(db: Session = Depends(get_db)):
    """List all ICP profiles."""
    return ICPService.list_icps(db)


@router.get("/{icp_id}", response_model=ICPResponse)
def get_icp(icp_id: int, db: Session = Depends(get_db)):
    """Get a specific ICP profile."""
    return ICPService.get_icp(db, icp_id)


@router.put("/{icp_id}", response_model=ICPResponse)
def update_icp(icp_id: int, icp_update: ICPUpdate, db: Session = Depends(get_db)):
    """Update an ICP profile."""
    return ICPService.update_icp(db, icp_id, icp_update)


@router.delete("/{icp_id}")
def delete_icp(icp_id: int, db: Session = Depends(get_db)):
    """Delete an ICP profile."""
    ICPService.delete_icp(db, icp_id)
    return {"message": "ICP profile deleted"}


@router.post("/templates/solo-founder", response_model=ICPResponse)
def create_solo_founder_icp(db: Session = Depends(get_db)):
    """Create a pre-built ICP for solo founders."""
    return ICPService.create_template_solo_founder(db)


@router.post("/templates/small-d2c", response_model=ICPResponse)
def create_small_d2c_icp(db: Session = Depends(get_db)):
    """Create a pre-built ICP for small D2C brands."""
    return ICPService.create_template_small_d2c(db)
