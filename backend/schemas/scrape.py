"""Web scraping schemas."""

from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class JobBoardScrapeRequest(BaseModel):
    """Request schema for scraping job boards."""

    query: str
    location: Optional[str] = ""
    sources: Optional[List[str]] = None  # ['indeed', 'naukri', 'linkedin']
    num_pages: Optional[int] = 3


class CompanyScrapeRequest(BaseModel):
    """Request schema for scraping a company website."""

    url: HttpUrl
    company_name: Optional[str] = None
    deep_scan: Optional[bool] = False


class LeadDiscoveryRequest(BaseModel):
    """Request schema for discovering leads via search."""

    search_query: str
    num_results: Optional[int] = 20
    scrape_companies: Optional[bool] = False


class CareerPageScrapeRequest(BaseModel):
    """Request schema for scraping a career page."""

    url: HttpUrl
    company_name: str
