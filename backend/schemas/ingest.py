"""Data ingest schemas for OCR and file uploads."""

from typing import List, Optional
from pydantic import BaseModel


class OCRResult(BaseModel):
    """Schema for OCR extraction result."""

    extracted_text: str
    detected_emails: List[str]
    detected_phones: List[str]
    detected_names: List[str]
    detected_company: Optional[str]


class CSVIngestResult(BaseModel):
    """Schema for CSV ingest result."""

    total_processed: int
    total_created: int
    message: str
