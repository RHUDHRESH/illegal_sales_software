"""Classification schemas."""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class SignalInput(BaseModel):
    """Schema for signal classification input."""

    signal_text: str
    source_type: str = "manual"
    source_url: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None


class ClassificationResult(BaseModel):
    """Schema for classification result."""

    icp_match: bool
    total_score: float
    score_bucket: str
    classification: Dict[str, Any]
    company_id: Optional[int]
    lead_id: Optional[int]
