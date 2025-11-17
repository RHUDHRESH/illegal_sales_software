"""
Scraping API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import logging

from ..scrapers.scraping_service import scraping_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scrape", tags=["scraping"])


class JobBoardScrapeRequest(BaseModel):
    """Request for scraping job boards"""
    query: str
    location: Optional[str] = ""
    sources: Optional[List[str]] = None  # ['indeed', 'naukri', 'linkedin']
    num_pages: Optional[int] = 3


class CompanyScrapeRequest(BaseModel):
    """Request for scraping a company website"""
    url: HttpUrl
    company_name: Optional[str] = None
    deep_scan: Optional[bool] = False


class LeadDiscoveryRequest(BaseModel):
    """Request for discovering leads via search"""
    search_query: str
    num_results: Optional[int] = 20
    scrape_companies: Optional[bool] = False


class CareerPageScrapeRequest(BaseModel):
    """Request for scraping a career page"""
    url: HttpUrl
    company_name: str


@router.post("/job-boards", summary="Scrape job boards for leads")
async def scrape_job_boards(
    request: JobBoardScrapeRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Scrape multiple job boards for job postings and create leads

    This endpoint scrapes job boards (Indeed, Naukri, LinkedIn) for job postings
    matching your query, then classifies them and creates leads automatically.

    **Parameters:**
    - **query**: Job search query (e.g., "marketing manager", "growth hacker")
    - **location**: Optional location filter
    - **sources**: List of sources to scrape ['indeed', 'naukri', 'linkedin'] (default: indeed, naukri)
    - **num_pages**: Number of pages to scrape per source (default: 3)

    **Returns:**
    - Results summary with jobs found and leads created

    **Example:**
    ```json
    {
        "query": "marketing manager",
        "location": "Mumbai",
        "sources": ["indeed", "naukri"],
        "num_pages": 3
    }
    ```
    """
    try:
        logger.info(f"Starting job board scrape: {request.query}")

        # Run scraping in background
        results = scraping_service.scrape_job_boards(
            query=request.query,
            location=request.location or "",
            sources=request.sources,
            num_pages=request.num_pages or 3
        )

        return {
            "status": "completed",
            "message": f"Scraped {results['total_jobs']} jobs, created {results['total_leads_created']} leads",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in job board scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company-website", summary="Scrape company website")
async def scrape_company_website(
    request: CompanyScrapeRequest
) -> Dict[str, Any]:
    """
    Scrape a company website for contact info and hiring signals

    This endpoint crawls a company website to extract:
    - Contact emails and phone numbers
    - Career page URLs
    - Job postings and hiring signals
    - Social media links
    - Technologies used
    - Company size hints

    **Parameters:**
    - **url**: Company website URL
    - **company_name**: Optional company name (auto-detected if not provided)
    - **deep_scan**: If true, also crawls career and contact pages (slower but more thorough)

    **Returns:**
    - Company data with contact info and any leads created

    **Example:**
    ```json
    {
        "url": "https://example.com",
        "company_name": "Example Corp",
        "deep_scan": true
    }
    ```
    """
    try:
        logger.info(f"Starting company website scrape: {request.url}")

        results = scraping_service.scrape_company_website(
            url=str(request.url),
            company_name=request.company_name,
            deep_scan=request.deep_scan or False
        )

        return {
            "status": "completed",
            "message": f"Scraped {request.url}, created {results['leads_created']} leads",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error scraping company website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover-leads", summary="Discover new leads via search")
async def discover_leads(
    request: LeadDiscoveryRequest
) -> Dict[str, Any]:
    """
    Discover new potential leads via search engines

    This endpoint searches the web for companies matching your criteria,
    then optionally scrapes each discovered company website.

    **Parameters:**
    - **search_query**: Search query (e.g., "D2C ecommerce India hiring marketing")
    - **num_results**: Number of search results to fetch (default: 20)
    - **scrape_companies**: If true, also scrapes each discovered company website (slower)

    **Returns:**
    - List of discovered URLs and leads created

    **Example:**
    ```json
    {
        "search_query": "SaaS startup India hiring growth marketing",
        "num_results": 30,
        "scrape_companies": true
    }
    ```
    """
    try:
        logger.info(f"Starting lead discovery: {request.search_query}")

        results = scraping_service.discover_leads(
            search_query=request.search_query,
            num_results=request.num_results or 20,
            scrape_companies=request.scrape_companies or False
        )

        return {
            "status": "completed",
            "message": f"Found {results['urls_found']} URLs, created {results['leads_created']} leads",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error discovering leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/career-page", summary="Scrape a career/jobs page")
async def scrape_career_page(
    request: CareerPageScrapeRequest
) -> Dict[str, Any]:
    """
    Scrape a specific career/jobs page for job postings

    This endpoint is useful when you know a company's career page URL
    and want to extract all job postings from it.

    **Parameters:**
    - **url**: Career page URL
    - **company_name**: Company name

    **Returns:**
    - Jobs found and leads created

    **Example:**
    ```json
    {
        "url": "https://example.com/careers",
        "company_name": "Example Corp"
    }
    ```
    """
    try:
        logger.info(f"Starting career page scrape: {request.url}")

        results = scraping_service.scrape_career_page(
            url=str(request.url),
            company_name=request.company_name
        )

        return {
            "status": "completed",
            "message": f"Found {results['jobs_found']} jobs, created {results['leads_created']} leads",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error scraping career page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", summary="List available scraping sources")
async def list_scraping_sources() -> Dict[str, Any]:
    """
    List all available scraping sources and their capabilities

    Returns information about which job boards and sources can be scraped.
    """
    return {
        "job_boards": [
            {
                "name": "indeed",
                "description": "Indeed.com - Global job board",
                "regions": ["Global"],
                "rate_limit": "2 seconds between requests"
            },
            {
                "name": "naukri",
                "description": "Naukri.com - Indian job board",
                "regions": ["India"],
                "rate_limit": "2 seconds between requests"
            },
            {
                "name": "linkedin",
                "description": "LinkedIn Jobs - Professional network (limited, may be blocked)",
                "regions": ["Global"],
                "rate_limit": "3 seconds between requests",
                "notes": "LinkedIn actively blocks scrapers, use with caution"
            }
        ],
        "search_engines": [
            {
                "name": "duckduckgo",
                "description": "DuckDuckGo search for lead discovery",
                "rate_limit": "2 seconds between requests"
            }
        ],
        "company_scraping": {
            "description": "Scrape any company website for contact info and hiring signals",
            "features": [
                "Extract contact emails and phones",
                "Find career page URLs",
                "Detect hiring signals",
                "Extract social media links",
                "Identify technologies used",
                "Estimate company size"
            ]
        }
    }


@router.get("/health", summary="Check scraping service health")
async def scraping_health() -> Dict[str, str]:
    """
    Check if scraping service is ready

    Returns the status of the scraping service.
    """
    return {
        "status": "healthy",
        "message": "Scraping service is ready"
    }
