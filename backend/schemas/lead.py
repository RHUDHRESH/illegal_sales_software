"""Lead, Company, and Contact schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CompanySimple(BaseModel):
    """Simplified company schema for nested responses."""

    id: int
    name: str
    website: Optional[str]
    sector: Optional[str]

    class Config:
        from_attributes = True


class ContactSimple(BaseModel):
    """Simplified contact schema for nested responses."""

    id: int
    name: Optional[str]
    role: Optional[str]
    email: Optional[str]
    phone_numbers: List

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    """Schema for lead response."""

    id: int
    company_id: int
    contact_id: Optional[int]
    score_icp_fit: float
    score_marketing_pain: float
    score_data_quality: float
    total_score: float
    score_bucket: str
    role_type: Optional[str]
    pain_tags: List
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
    """Schema for filtering leads."""

    score_min: int = 0
    score_max: int = 100
    status: Optional[str] = None
    score_bucket: Optional[str] = None
    limit: int = 50
    offset: int = 0


class LeadStatusUpdate(BaseModel):
    """Schema for updating lead status."""

    status: str


class LeadNotesUpdate(BaseModel):
    """Schema for updating lead notes."""

    notes: str
