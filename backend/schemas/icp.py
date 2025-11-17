"""ICP (Ideal Customer Profile) schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ICPCreate(BaseModel):
    """Schema for creating a new ICP profile."""

    name: str
    description: Optional[str] = None
    size_buckets: List[str] = []
    industries: List[str] = []
    locations: List[str] = []
    stages: List[str] = []
    hiring_keywords: List[str] = []
    pain_keywords: List[str] = []
    channel_preferences: List[str] = []
    budget_signals: List[str] = []


class ICPUpdate(BaseModel):
    """Schema for updating an existing ICP profile."""

    name: Optional[str] = None
    description: Optional[str] = None
    size_buckets: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    stages: Optional[List[str]] = None
    hiring_keywords: Optional[List[str]] = None
    pain_keywords: Optional[List[str]] = None
    channel_preferences: Optional[List[str]] = None
    budget_signals: Optional[List[str]] = None


class ICPResponse(BaseModel):
    """Schema for ICP profile response."""

    id: int
    name: str
    description: Optional[str] = None
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
