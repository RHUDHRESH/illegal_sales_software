"""ICP (Ideal Customer Profile) business logic service."""

from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import ICPProfile
from schemas.icp import ICPCreate, ICPUpdate


class ICPService:
    """Service for managing ICP profiles."""

    @staticmethod
    def create_icp(db: Session, icp_data: ICPCreate) -> ICPProfile:
        """
        Create a new ICP profile.

        Args:
            db: Database session
            icp_data: ICP creation data

        Returns:
            Created ICP profile

        Raises:
            HTTPException: If ICP with same name already exists
        """
        # Check if name already exists
        existing = db.query(ICPProfile).filter(ICPProfile.name == icp_data.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="ICP profile with this name already exists"
            )

        # Create new ICP profile
        db_icp = ICPProfile(
            name=icp_data.name,
            description=icp_data.description,
            size_buckets=icp_data.size_buckets,
            industries=icp_data.industries,
            locations=icp_data.locations,
            stages=icp_data.stages,
            hiring_keywords=icp_data.hiring_keywords,
            pain_keywords=icp_data.pain_keywords,
            channel_preferences=icp_data.channel_preferences,
            budget_signals=icp_data.budget_signals,
        )
        db.add(db_icp)
        db.commit()
        db.refresh(db_icp)
        return db_icp

    @staticmethod
    def list_icps(db: Session) -> List[ICPProfile]:
        """
        List all ICP profiles.

        Args:
            db: Database session

        Returns:
            List of ICP profiles
        """
        return db.query(ICPProfile).all()

    @staticmethod
    def get_icp(db: Session, icp_id: int) -> ICPProfile:
        """
        Get a specific ICP profile.

        Args:
            db: Database session
            icp_id: ICP profile ID

        Returns:
            ICP profile

        Raises:
            HTTPException: If ICP not found
        """
        icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
        if not icp:
            raise HTTPException(status_code=404, detail="ICP profile not found")
        return icp

    @staticmethod
    def update_icp(db: Session, icp_id: int, icp_update: ICPUpdate) -> ICPProfile:
        """
        Update an ICP profile.

        Args:
            db: Database session
            icp_id: ICP profile ID
            icp_update: Update data

        Returns:
            Updated ICP profile

        Raises:
            HTTPException: If ICP not found
        """
        icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
        if not icp:
            raise HTTPException(status_code=404, detail="ICP profile not found")

        # Update fields if provided
        update_data = icp_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(icp, key, value)

        icp.updated_at = datetime.utcnow()
        db.add(icp)
        db.commit()
        db.refresh(icp)
        return icp

    @staticmethod
    def delete_icp(db: Session, icp_id: int) -> None:
        """
        Delete an ICP profile.

        Args:
            db: Database session
            icp_id: ICP profile ID

        Raises:
            HTTPException: If ICP not found
        """
        icp = db.query(ICPProfile).filter(ICPProfile.id == icp_id).first()
        if not icp:
            raise HTTPException(status_code=404, detail="ICP profile not found")

        db.delete(icp)
        db.commit()

    @staticmethod
    def create_template_solo_founder(db: Session) -> ICPProfile:
        """Create a pre-built ICP template for solo founders."""
        icp_data = ICPCreate(
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
        return ICPService.create_icp(db, icp_data)

    @staticmethod
    def create_template_small_d2c(db: Session) -> ICPProfile:
        """Create a pre-built ICP template for small D2C brands."""
        icp_data = ICPCreate(
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
        return ICPService.create_icp(db, icp_data)
