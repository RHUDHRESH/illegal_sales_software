"""Job board API integration for Naukri, LinkedIn, and other platforms.

This module provides integrations with job board APIs to fetch marketing roles
and ingest them as signals. Credentials should be stored in environment variables.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class JobBoardConfig(BaseModel):
    """Configuration for job board API access."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: str
    rate_limit_seconds: float = 2.0


class JobResult(BaseModel):
    """Standardized job result from any job board."""
    title: str
    company_name: str
    location: Optional[str] = None
    description: str
    posted_at: Optional[str] = None
    url: Optional[str] = None
    salary: Optional[str] = None
    experience_required: Optional[str] = None
    source_board: str


# ============================================================================
# Naukri API Integration
# ============================================================================

class NaukriAPI:
    """
    Integration with Naukri.com API.

    Note: Naukri requires API access credentials. Contact Naukri for API access.
    Set environment variables:
    - NAUKRI_API_KEY
    - NAUKRI_API_SECRET
    """

    def __init__(self):
        self.api_key = os.getenv("NAUKRI_API_KEY")
        self.api_secret = os.getenv("NAUKRI_API_SECRET")
        self.base_url = "https://api.naukri.com/v3"  # Example URL (not official)

        if not self.api_key:
            logger.warning("NAUKRI_API_KEY not set. Naukri API integration will not work.")

    async def search_marketing_jobs(
        self,
        keywords: List[str] = None,
        location: str = "India",
        experience: str = None,
        max_results: int = 20
    ) -> List[JobResult]:
        """
        Search for marketing jobs on Naukri.

        Args:
            keywords: Search keywords (default: ["marketing manager", "growth hacker"])
            location: Job location
            experience: Experience level (e.g., "0-2", "2-5")
            max_results: Maximum number of results to return

        Returns:
            List of standardized JobResult objects
        """
        if not self.api_key:
            raise ValueError("NAUKRI_API_KEY not set. Cannot fetch jobs from Naukri.")

        if keywords is None:
            keywords = ["marketing manager", "growth hacker", "digital marketing"]

        jobs = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for keyword in keywords:
                try:
                    # Example API call (adjust based on actual Naukri API)
                    params = {
                        "keywords": keyword,
                        "location": location,
                        "experience": experience or "",
                        "limit": max_results,
                    }

                    headers = {
                        "X-API-Key": self.api_key,
                        "X-API-Secret": self.api_secret or "",
                    }

                    # NOTE: This is a placeholder - actual Naukri API endpoint may differ
                    response = await client.get(
                        f"{self.base_url}/jobs/search",
                        params=params,
                        headers=headers
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Parse response (adjust based on actual API response structure)
                        for job in data.get("jobs", [])[:max_results]:
                            jobs.append(JobResult(
                                title=job.get("title", ""),
                                company_name=job.get("company", ""),
                                location=job.get("location", ""),
                                description=job.get("description", ""),
                                posted_at=job.get("posted_date", ""),
                                url=job.get("job_url", ""),
                                salary=job.get("salary", ""),
                                experience_required=job.get("experience", ""),
                                source_board="naukri",
                            ))
                    else:
                        logger.error(f"Naukri API error: {response.status_code}")

                except Exception as e:
                    logger.error(f"Error fetching Naukri jobs for keyword '{keyword}': {e}")

        return jobs


# ============================================================================
# LinkedIn Jobs API Integration
# ============================================================================

class LinkedInJobsAPI:
    """
    Integration with LinkedIn Jobs API.

    Note: LinkedIn has strict API access policies. You need to:
    1. Apply for LinkedIn Partner Program
    2. Get approved for Jobs API access
    3. Obtain OAuth credentials

    Set environment variables:
    - LINKEDIN_CLIENT_ID
    - LINKEDIN_CLIENT_SECRET
    - LINKEDIN_ACCESS_TOKEN
    """

    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.base_url = "https://api.linkedin.com/v2"

        if not self.access_token:
            logger.warning("LINKEDIN_ACCESS_TOKEN not set. LinkedIn API integration will not work.")

    async def search_marketing_jobs(
        self,
        keywords: List[str] = None,
        location: str = "India",
        max_results: int = 20
    ) -> List[JobResult]:
        """
        Search for marketing jobs on LinkedIn.

        Args:
            keywords: Search keywords
            location: Job location
            max_results: Maximum number of results

        Returns:
            List of standardized JobResult objects
        """
        if not self.access_token:
            raise ValueError("LINKEDIN_ACCESS_TOKEN not set. Cannot fetch jobs from LinkedIn.")

        if keywords is None:
            keywords = ["marketing manager", "growth hacker", "digital marketing"]

        jobs = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # LinkedIn Jobs API endpoint (example - actual endpoint may differ)
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                }

                params = {
                    "keywords": ",".join(keywords),
                    "location": location,
                    "count": max_results,
                }

                # NOTE: This is a placeholder - actual LinkedIn API requires proper OAuth flow
                response = await client.get(
                    f"{self.base_url}/jobs",
                    params=params,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()

                    # Parse response (adjust based on actual API response structure)
                    for job in data.get("elements", [])[:max_results]:
                        jobs.append(JobResult(
                            title=job.get("title", ""),
                            company_name=job.get("companyName", ""),
                            location=job.get("location", ""),
                            description=job.get("description", {}).get("text", ""),
                            posted_at=job.get("listedAt", ""),
                            url=job.get("applyMethod", {}).get("companyApplyUrl", ""),
                            salary=None,  # LinkedIn often doesn't provide salary via API
                            experience_required=job.get("experienceLevel", ""),
                            source_board="linkedin",
                        ))
                else:
                    logger.error(f"LinkedIn API error: {response.status_code}")

            except Exception as e:
                logger.error(f"Error fetching LinkedIn jobs: {e}")

        return jobs


# ============================================================================
# Generic Job Board API Client
# ============================================================================

class JobBoardAPIClient:
    """
    Unified client for all job board APIs.
    """

    def __init__(self):
        self.naukri = NaukriAPI()
        self.linkedin = LinkedInJobsAPI()

    async def fetch_all_marketing_jobs(
        self,
        boards: List[str] = None,
        keywords: List[str] = None,
        location: str = "India",
        max_results_per_board: int = 20
    ) -> List[JobResult]:
        """
        Fetch marketing jobs from multiple job boards.

        Args:
            boards: List of boards to query (default: ["naukri", "linkedin"])
            keywords: Search keywords
            location: Job location
            max_results_per_board: Max results per board

        Returns:
            Combined list of JobResult objects from all boards
        """
        if boards is None:
            boards = ["naukri", "linkedin"]

        all_jobs = []

        for board in boards:
            try:
                if board == "naukri" and self.naukri.api_key:
                    jobs = await self.naukri.search_marketing_jobs(
                        keywords=keywords,
                        location=location,
                        max_results=max_results_per_board
                    )
                    all_jobs.extend(jobs)
                    logger.info(f"Fetched {len(jobs)} jobs from Naukri")

                elif board == "linkedin" and self.linkedin.access_token:
                    jobs = await self.linkedin.search_marketing_jobs(
                        keywords=keywords,
                        location=location,
                        max_results=max_results_per_board
                    )
                    all_jobs.extend(jobs)
                    logger.info(f"Fetched {len(jobs)} jobs from LinkedIn")

                else:
                    logger.warning(f"Skipping {board} - credentials not configured")

            except Exception as e:
                logger.error(f"Error fetching jobs from {board}: {e}")

        return all_jobs


# ============================================================================
# Helper Functions
# ============================================================================

def job_to_signal_text(job: JobResult) -> str:
    """
    Convert a JobResult to signal text for classification.
    """
    parts = [f"Job Title: {job.title}"]

    if job.location:
        parts.append(f"Location: {job.location}")

    if job.experience_required:
        parts.append(f"Experience Required: {job.experience_required}")

    if job.salary:
        parts.append(f"Salary: {job.salary}")

    if job.posted_at:
        parts.append(f"Posted: {job.posted_at}")

    parts.append(f"Description:\n{job.description}")

    return "\n".join(parts)
