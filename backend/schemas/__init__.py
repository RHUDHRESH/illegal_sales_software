"""Centralized Pydantic schemas for API requests and responses."""

from .icp import ICPCreate, ICPUpdate, ICPResponse
from .lead import (
    CompanySimple,
    ContactSimple,
    LeadResponse,
    LeadFilter,
    LeadStatusUpdate,
    LeadNotesUpdate,
)
from .classification import SignalInput, ClassificationResult
from .ingest import OCRResult, CSVIngestResult
from .scrape import (
    JobBoardScrapeRequest,
    CompanyScrapeRequest,
    LeadDiscoveryRequest,
    CareerPageScrapeRequest,
)

__all__ = [
    # ICP schemas
    "ICPCreate",
    "ICPUpdate",
    "ICPResponse",
    # Lead schemas
    "CompanySimple",
    "ContactSimple",
    "LeadResponse",
    "LeadFilter",
    "LeadStatusUpdate",
    "LeadNotesUpdate",
    # Classification schemas
    "SignalInput",
    "ClassificationResult",
    # Ingest schemas
    "OCRResult",
    "CSVIngestResult",
    # Scrape schemas
    "JobBoardScrapeRequest",
    "CompanyScrapeRequest",
    "LeadDiscoveryRequest",
    "CareerPageScrapeRequest",
]
