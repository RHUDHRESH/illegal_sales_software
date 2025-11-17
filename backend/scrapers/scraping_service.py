"""
Scraping orchestration service - coordinates all scrapers and processes results
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from .job_scrapers import IndeedScraper, NaukriScraper, LinkedInJobsScraper, GenericJobScraper
from .company_scraper import CompanyScraper, LeadDiscoveryScraper
from ..database import Company, Contact, Signal, Lead, SessionLocal
from ..ollama_wrapper import classify_signal_with_ollama

logger = logging.getLogger(__name__)


class ScrapingService:
    """
    Orchestrates scraping operations and processes results
    """

    def __init__(self):
        self.indeed_scraper = IndeedScraper(rate_limit=2.0)
        self.naukri_scraper = NaukriScraper(rate_limit=2.0)
        self.linkedin_scraper = LinkedInJobsScraper(rate_limit=3.0)  # Slower for LinkedIn
        self.company_scraper = CompanyScraper(rate_limit=2.0)
        self.lead_discovery = LeadDiscoveryScraper(rate_limit=2.0)
        self.generic_job_scraper = GenericJobScraper(rate_limit=2.0)
        self.executor = ThreadPoolExecutor(max_workers=3)

    def scrape_job_boards(
        self,
        query: str,
        location: str = "",
        sources: List[str] = None,
        num_pages: int = 3
    ) -> Dict[str, Any]:
        """
        Scrape multiple job boards and process results

        Args:
            query: Job search query (e.g., "marketing manager")
            location: Location filter
            sources: List of sources to scrape ['indeed', 'naukri', 'linkedin'] or None for all
            num_pages: Number of pages per source

        Returns:
            Dictionary with scraping results and stats
        """
        if sources is None:
            sources = ['indeed', 'naukri']  # Exclude LinkedIn by default (more restrictive)

        results = {
            'query': query,
            'location': location,
            'started_at': datetime.now().isoformat(),
            'sources': {},
            'total_jobs': 0,
            'total_leads_created': 0,
            'errors': []
        }

        all_jobs = []

        # Scrape each source
        for source in sources:
            try:
                logger.info(f"Scraping {source} for: {query}")
                jobs = []

                if source == 'indeed':
                    jobs = self.indeed_scraper.scrape_jobs(query, location, num_pages)
                elif source == 'naukri':
                    jobs = self.naukri_scraper.scrape_jobs(query, location, num_pages)
                elif source == 'linkedin':
                    jobs = self.linkedin_scraper.scrape_jobs(query, location, num_pages)

                results['sources'][source] = {
                    'jobs_found': len(jobs),
                    'status': 'success'
                }

                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {source}")

            except Exception as e:
                logger.error(f"Error scraping {source}: {e}")
                results['sources'][source] = {
                    'jobs_found': 0,
                    'status': 'error',
                    'error': str(e)
                }
                results['errors'].append(f"{source}: {str(e)}")

        results['total_jobs'] = len(all_jobs)

        # Process and store jobs
        try:
            leads_created = self._process_job_postings(all_jobs)
            results['total_leads_created'] = leads_created
        except Exception as e:
            logger.error(f"Error processing job postings: {e}")
            results['errors'].append(f"Processing error: {str(e)}")

        results['completed_at'] = datetime.now().isoformat()
        return results

    def scrape_company_website(
        self,
        url: str,
        company_name: Optional[str] = None,
        deep_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a company website for contact info and job signals

        Args:
            url: Company website URL
            company_name: Optional company name (will be extracted if not provided)
            deep_scan: If True, crawl career and contact pages

        Returns:
            Dictionary with company data and scraping results
        """
        results = {
            'url': url,
            'started_at': datetime.now().isoformat(),
            'company_data': None,
            'leads_created': 0,
            'error': None
        }

        try:
            logger.info(f"Scraping company website: {url}")
            company_data = self.company_scraper.scrape_company(url, deep_scan)

            if company_name:
                company_data['name'] = company_name

            results['company_data'] = company_data

            # Process company data and create leads if hiring signals found
            if company_data.get('has_jobs') or company_data.get('job_signals'):
                leads_created = self._process_company_data(company_data)
                results['leads_created'] = leads_created

        except Exception as e:
            logger.error(f"Error scraping company website {url}: {e}")
            results['error'] = str(e)

        results['completed_at'] = datetime.now().isoformat()
        return results

    def discover_leads(
        self,
        search_query: str,
        num_results: int = 20,
        scrape_companies: bool = False
    ) -> Dict[str, Any]:
        """
        Discover new leads via search engines

        Args:
            search_query: Search query (e.g., "D2C ecommerce India hiring")
            num_results: Number of search results to fetch
            scrape_companies: If True, also scrape each discovered company website

        Returns:
            Dictionary with discovered leads
        """
        results = {
            'query': search_query,
            'started_at': datetime.now().isoformat(),
            'urls_found': 0,
            'companies_scraped': 0,
            'leads_created': 0,
            'discovered_urls': [],
            'errors': []
        }

        try:
            # Search for leads
            logger.info(f"Discovering leads with query: {search_query}")
            search_results = self.lead_discovery.search_for_leads(search_query, num_results)

            results['urls_found'] = len(search_results)
            results['discovered_urls'] = [r['url'] for r in search_results]

            # Optionally scrape each discovered company
            if scrape_companies:
                for result in search_results:
                    try:
                        company_url = result['url']
                        logger.info(f"Scraping discovered company: {company_url}")

                        company_result = self.scrape_company_website(
                            company_url,
                            deep_scan=False  # Quick scan for discovery
                        )

                        results['companies_scraped'] += 1
                        results['leads_created'] += company_result.get('leads_created', 0)

                    except Exception as e:
                        logger.error(f"Error scraping discovered company {company_url}: {e}")
                        results['errors'].append(f"{company_url}: {str(e)}")

        except Exception as e:
            logger.error(f"Error discovering leads: {e}")
            results['errors'].append(str(e))

        results['completed_at'] = datetime.now().isoformat()
        return results

    def scrape_career_page(self, url: str, company_name: str) -> Dict[str, Any]:
        """
        Scrape a specific career/jobs page

        Args:
            url: Career page URL
            company_name: Company name

        Returns:
            Dictionary with jobs found and leads created
        """
        results = {
            'url': url,
            'company_name': company_name,
            'started_at': datetime.now().isoformat(),
            'jobs_found': 0,
            'leads_created': 0,
            'error': None
        }

        try:
            logger.info(f"Scraping career page: {url}")
            jobs = self.generic_job_scraper.scrape_career_page(url)

            results['jobs_found'] = len(jobs)

            # Add company name to each job
            for job in jobs:
                job['company'] = company_name

            # Process jobs
            if jobs:
                leads_created = self._process_job_postings(jobs)
                results['leads_created'] = leads_created

        except Exception as e:
            logger.error(f"Error scraping career page {url}: {e}")
            results['error'] = str(e)

        results['completed_at'] = datetime.now().isoformat()
        return results

    def _process_job_postings(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Process job postings and create leads

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of leads created
        """
        leads_created = 0
        db = SessionLocal()

        try:
            for job in jobs:
                try:
                    company_name = job.get('company')
                    if not company_name:
                        continue

                    # Get or create company
                    company = self._get_or_create_company(db, company_name, job.get('url'))

                    # Create signal from job posting
                    signal_text = self._format_job_signal(job)

                    # Check for duplicate signals
                    existing_signal = db.query(Signal).filter(
                        Signal.company_id == company.id,
                        Signal.raw_text == signal_text
                    ).first()

                    if existing_signal:
                        logger.debug(f"Duplicate signal for {company_name}, skipping")
                        continue

                    # Create signal
                    signal = Signal(
                        company_id=company.id,
                        raw_text=signal_text,
                        source_type='job_post',
                        source_url=job.get('url')
                    )
                    db.add(signal)
                    db.flush()

                    # Classify signal and create lead
                    try:
                        classification = classify_signal_with_ollama(
                            signal_text=signal_text,
                            company_name=company_name,
                            company_website=company.website
                        )

                        if classification and classification.get('icp_match'):
                            # Create lead
                            lead = self._create_lead_from_classification(
                                db, company, signal, classification
                            )
                            if lead:
                                leads_created += 1

                    except Exception as e:
                        logger.error(f"Error classifying signal for {company_name}: {e}")

                except Exception as e:
                    logger.error(f"Error processing job posting: {e}")
                    continue

            db.commit()

        except Exception as e:
            logger.error(f"Error in _process_job_postings: {e}")
            db.rollback()
        finally:
            db.close()

        return leads_created

    def _process_company_data(self, company_data: Dict[str, Any]) -> int:
        """
        Process company data and create leads from hiring signals

        Args:
            company_data: Company data dictionary

        Returns:
            Number of leads created
        """
        leads_created = 0
        db = SessionLocal()

        try:
            company_name = company_data.get('name')
            company_url = company_data.get('url')

            if not company_name:
                return 0

            # Get or create company
            company = self._get_or_create_company(db, company_name, company_url)

            # Update company with scraped data
            if company_data.get('description'):
                company.description = company_data['description']
            if company_data.get('career_page_url'):
                company.metadata = company.metadata or {}
                company.metadata['career_page_url'] = company_data['career_page_url']

            # Create contacts from emails
            for email in company_data.get('emails', [])[:5]:  # Limit to 5
                self._get_or_create_contact(db, company, email=email)

            # Create contacts from phones
            for phone in company_data.get('phones', [])[:5]:  # Limit to 5
                self._get_or_create_contact(db, company, phone=phone)

            # Process job signals
            for job_signal in company_data.get('job_signals', []):
                try:
                    # Check for duplicate
                    existing_signal = db.query(Signal).filter(
                        Signal.company_id == company.id,
                        Signal.raw_text == job_signal
                    ).first()

                    if existing_signal:
                        continue

                    # Create signal
                    signal = Signal(
                        company_id=company.id,
                        raw_text=job_signal,
                        source_type='website',
                        source_url=company_url
                    )
                    db.add(signal)
                    db.flush()

                    # Classify and create lead
                    try:
                        classification = classify_signal_with_ollama(
                            signal_text=job_signal,
                            company_name=company_name,
                            company_website=company_url
                        )

                        if classification and classification.get('icp_match'):
                            lead = self._create_lead_from_classification(
                                db, company, signal, classification
                            )
                            if lead:
                                leads_created += 1

                    except Exception as e:
                        logger.error(f"Error classifying signal: {e}")

                except Exception as e:
                    logger.error(f"Error processing job signal: {e}")
                    continue

            db.commit()

        except Exception as e:
            logger.error(f"Error in _process_company_data: {e}")
            db.rollback()
        finally:
            db.close()

        return leads_created

    def _get_or_create_company(
        self,
        db: Session,
        name: str,
        website: Optional[str] = None
    ) -> Company:
        """Get or create company record"""
        # Try to find existing company
        query = db.query(Company)

        if website:
            # Try by website first
            company = query.filter(Company.website == website).first()
            if company:
                return company

        # Try by name (case-insensitive)
        company = query.filter(Company.name.ilike(name)).first()
        if company:
            # Update website if provided and not set
            if website and not company.website:
                company.website = website
                db.flush()
            return company

        # Create new company
        company = Company(
            name=name,
            website=website
        )
        db.add(company)
        db.flush()
        return company

    def _get_or_create_contact(
        self,
        db: Session,
        company: Company,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[Contact]:
        """Get or create contact record"""
        if not email and not phone:
            return None

        # Try to find existing
        query = db.query(Contact).filter(Contact.company_id == company.id)

        if email:
            contact = query.filter(Contact.email == email).first()
            if contact:
                return contact

        if phone:
            contact = query.filter(Contact.phone == phone).first()
            if contact:
                return contact

        # Create new
        contact = Contact(
            company_id=company.id,
            email=email,
            phone=phone
        )
        db.add(contact)
        db.flush()
        return contact

    def _create_lead_from_classification(
        self,
        db: Session,
        company: Company,
        signal: Signal,
        classification: Dict[str, Any]
    ) -> Optional[Lead]:
        """Create lead from classification results"""
        try:
            # Check if lead already exists for this company
            existing_lead = db.query(Lead).filter(
                Lead.company_id == company.id
            ).first()

            if existing_lead:
                # Update if new score is higher
                new_score = classification.get('total_score', 0)
                if new_score > (existing_lead.total_score or 0):
                    # Update lead with new data
                    for key, value in classification.items():
                        if hasattr(existing_lead, key):
                            setattr(existing_lead, key, value)
                    db.flush()
                    return existing_lead
                else:
                    return None  # Don't create duplicate

            # Create new lead
            lead = Lead(
                company_id=company.id,
                signal_id=signal.id,
                **classification
            )
            db.add(lead)
            db.flush()
            return lead

        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return None

    def _format_job_signal(self, job: Dict[str, Any]) -> str:
        """Format job posting as signal text"""
        parts = []

        if job.get('title'):
            parts.append(f"Job Title: {job['title']}")

        if job.get('company'):
            parts.append(f"Company: {job['company']}")

        if job.get('location'):
            parts.append(f"Location: {job['location']}")

        if job.get('description'):
            parts.append(f"Description: {job['description']}")

        if job.get('experience'):
            parts.append(f"Experience: {job['experience']}")

        if job.get('salary'):
            parts.append(f"Salary: {job['salary']}")

        return "\n".join(parts)


# Global instance
scraping_service = ScrapingService()
