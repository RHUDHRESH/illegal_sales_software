"""Lead management business logic service."""

from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Lead


class LeadService:
    """Service for managing leads."""

    VALID_STATUSES = ["new", "contacted", "qualified", "pitched", "trial", "won", "lost", "parked"]

    @staticmethod
    def list_leads(
        db: Session,
        score_min: int = 0,
        score_max: int = 100,
        status: Optional[str] = None,
        score_bucket: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Lead]:
        """
        List leads with filtering.

        Args:
            db: Database session
            score_min: Minimum score filter
            score_max: Maximum score filter
            status: Status filter
            score_bucket: Score bucket filter
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of filtered leads
        """
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

    @staticmethod
    def get_lead(db: Session, lead_id: int) -> Lead:
        """
        Get a specific lead.

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            Lead

        Raises:
            HTTPException: If lead not found
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead

    @staticmethod
    def update_lead_status(db: Session, lead_id: int, status: str) -> Lead:
        """
        Update lead status.

        Args:
            db: Database session
            lead_id: Lead ID
            status: New status

        Returns:
            Updated lead

        Raises:
            HTTPException: If lead not found or invalid status
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        if status not in LeadService.VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {LeadService.VALID_STATUSES}"
            )

        lead.status = status
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def update_lead_notes(db: Session, lead_id: int, notes: str) -> Lead:
        """
        Update lead notes.

        Args:
            db: Database session
            lead_id: Lead ID
            notes: New notes

        Returns:
            Updated lead

        Raises:
            HTTPException: If lead not found
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead.notes = notes
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def get_bucket_counts(db: Session) -> dict:
        """
        Get count of leads by score bucket.

        Args:
            db: Database session

        Returns:
            Dictionary with counts per bucket
        """
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

    @staticmethod
    def delete_lead(db: Session, lead_id: int) -> None:
        """
        Delete a lead.

        Args:
            db: Database session
            lead_id: Lead ID

        Raises:
            HTTPException: If lead not found
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        db.delete(lead)
        db.commit()
