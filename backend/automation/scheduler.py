"""
Automated Scheduling for Lead Generation Tasks
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import json

from sqlalchemy.orm import Session
from ..database import SessionLocal, Lead, Company
from ..scrapers.scraping_service import scraping_service
from ..enrichment.company_enrichment import company_enrichment

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Manages scheduled jobs for automated lead generation
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        self.job_history = []

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")

    def add_daily_job_scrape(
        self,
        job_id: str,
        query: str,
        sources: List[str] = None,
        hour: int = 9,
        minute: int = 0
    ):
        """
        Schedule daily job board scraping

        Args:
            job_id: Unique job identifier
            query: Job search query
            sources: List of job boards to scrape
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        if sources is None:
            sources = ["indeed", "naukri"]

        def job_func():
            logger.info(f"Running scheduled job scrape: {query}")
            try:
                results = scraping_service.scrape_job_boards(
                    query=query,
                    sources=sources,
                    num_pages=3
                )
                self._log_job_run(job_id, "job_scrape", results)
                logger.info(f"Job scrape completed: {results.get('total_leads_created', 0)} leads created")
            except Exception as e:
                logger.error(f"Error in scheduled job scrape: {e}")
                self._log_job_run(job_id, "job_scrape", {"error": str(e)})

        job = self.scheduler.add_job(
            job_func,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "job_scrape",
            "query": query,
            "sources": sources,
            "schedule": f"Daily at {hour:02d}:{minute:02d}",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Scheduled daily job scrape: {job_id}")
        return job

    def add_enrichment_job(
        self,
        job_id: str,
        interval_hours: int = 24
    ):
        """
        Schedule periodic company enrichment for existing leads

        Enriches companies that don't have complete data
        """
        def enrichment_func():
            logger.info("Running scheduled enrichment job")
            db = SessionLocal()
            try:
                # Get companies that need enrichment (missing key fields)
                companies = db.query(Company).filter(
                    (Company.description == None) |
                    (Company.metadata == None)
                ).limit(50).all()

                enriched_count = 0
                for company in companies:
                    if not company.website:
                        continue

                    try:
                        enrichment_data = company_enrichment.enrich_company(
                            company_name=company.name,
                            website=company.website,
                            deep=False
                        )

                        # Update company with enrichment data
                        if enrichment_data.get("description"):
                            company.description = enrichment_data["description"]

                        if not company.metadata:
                            company.metadata = {}

                        company.metadata.update({
                            "enrichment": enrichment_data,
                            "enriched_at": datetime.now().isoformat()
                        })

                        enriched_count += 1

                    except Exception as e:
                        logger.error(f"Error enriching company {company.name}: {e}")
                        continue

                db.commit()
                self._log_job_run(job_id, "enrichment", {"enriched_count": enriched_count})
                logger.info(f"Enrichment job completed: {enriched_count} companies enriched")

            except Exception as e:
                logger.error(f"Error in enrichment job: {e}")
                self._log_job_run(job_id, "enrichment", {"error": str(e)})
                db.rollback()
            finally:
                db.close()

        job = self.scheduler.add_job(
            enrichment_func,
            IntervalTrigger(hours=interval_hours),
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "enrichment",
            "interval_hours": interval_hours,
            "schedule": f"Every {interval_hours} hours",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Scheduled enrichment job: {job_id}")
        return job

    def add_lead_discovery_job(
        self,
        job_id: str,
        search_queries: List[str],
        interval_hours: int = 168  # Weekly by default
    ):
        """
        Schedule periodic lead discovery via search engines

        Args:
            job_id: Job identifier
            search_queries: List of search queries to discover leads
            interval_hours: How often to run (default: weekly)
        """
        def discovery_func():
            logger.info("Running scheduled lead discovery")
            total_leads = 0

            for query in search_queries:
                try:
                    results = scraping_service.discover_leads(
                        search_query=query,
                        num_results=20,
                        scrape_companies=True
                    )
                    total_leads += results.get("leads_created", 0)
                except Exception as e:
                    logger.error(f"Error in lead discovery for query '{query}': {e}")

            self._log_job_run(job_id, "lead_discovery", {"total_leads": total_leads})
            logger.info(f"Lead discovery completed: {total_leads} leads created")

        job = self.scheduler.add_job(
            discovery_func,
            IntervalTrigger(hours=interval_hours),
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "lead_discovery",
            "queries": search_queries,
            "interval_hours": interval_hours,
            "schedule": f"Every {interval_hours} hours",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Scheduled lead discovery job: {job_id}")
        return job

    def add_contact_enrichment_job(
        self,
        job_id: str,
        interval_hours: int = 48
    ):
        """
        Schedule contact finding for companies without contact info

        Finds emails and phones for companies in the database
        """
        def contact_func():
            logger.info("Running scheduled contact enrichment")
            db = SessionLocal()
            try:
                from ..enrichment.contact_finder import contact_finder

                # Get companies without contact info
                companies = db.query(Company).filter(
                    ~Company.contacts.any()  # No contacts
                ).limit(30).all()

                contacts_found = 0
                for company in companies:
                    if not company.website:
                        continue

                    try:
                        # Find contacts
                        candidates = contact_finder.find_contacts(
                            company_name=company.name,
                            website=company.website
                        )

                        # Store top candidates in metadata
                        if candidates:
                            if not company.metadata:
                                company.metadata = {}

                            company.metadata["email_candidates"] = [
                                {
                                    "email": c.email,
                                    "confidence": c.confidence,
                                    "verified": c.deliverable
                                }
                                for c in candidates[:5]  # Top 5
                            ]

                            contacts_found += len(candidates)

                    except Exception as e:
                        logger.error(f"Error finding contacts for {company.name}: {e}")
                        continue

                db.commit()
                self._log_job_run(job_id, "contact_enrichment", {"contacts_found": contacts_found})
                logger.info(f"Contact enrichment completed: {contacts_found} contacts found")

            except Exception as e:
                logger.error(f"Error in contact enrichment job: {e}")
                self._log_job_run(job_id, "contact_enrichment", {"error": str(e)})
                db.rollback()
            finally:
                db.close()

        job = self.scheduler.add_job(
            contact_func,
            IntervalTrigger(hours=interval_hours),
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "contact_enrichment",
            "interval_hours": interval_hours,
            "schedule": f"Every {interval_hours} hours",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Scheduled contact enrichment job: {job_id}")
        return job

    def add_custom_job(
        self,
        job_id: str,
        func: Callable,
        trigger: str = "interval",
        **trigger_args
    ):
        """
        Add a custom scheduled job

        Args:
            job_id: Job identifier
            func: Function to execute
            trigger: Type of trigger ('interval', 'cron', 'date')
            **trigger_args: Arguments for the trigger
        """
        if trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_args)
        elif trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        else:
            raise ValueError(f"Unsupported trigger type: {trigger}")

        job = self.scheduler.add_job(
            func,
            trigger_obj,
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "custom",
            "trigger": trigger,
            "trigger_args": trigger_args,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Scheduled custom job: {job_id}")
        return job

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        jobs_list = []
        for job_id, job_data in self.jobs.items():
            job = self.scheduler.get_job(job_id)
            jobs_list.append({
                "id": job_id,
                "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
                **job_data
            })
        return jobs_list

    def get_job_history(self, job_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get job execution history"""
        history = self.job_history[-limit:]
        if job_id:
            history = [h for h in history if h["job_id"] == job_id]
        return history

    def _log_job_run(self, job_id: str, job_type: str, result: Dict[str, Any]):
        """Log job execution"""
        log_entry = {
            "job_id": job_id,
            "job_type": job_type,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        self.job_history.append(log_entry)

        # Keep only last 1000 entries
        if len(self.job_history) > 1000:
            self.job_history = self.job_history[-1000:]


# Global scheduler instance
job_scheduler = JobScheduler()
