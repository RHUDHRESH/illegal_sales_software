"""Scheduled tasks for periodic job board scraping and data ingestion.

This module uses APScheduler to run periodic tasks such as:
- Daily job board API polling
- RSS feed monitoring
- Re-scraping company websites
"""

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import List, Optional

from job_board_apis import JobBoardAPIClient, job_to_signal_text
from routers.classify import SignalInput, classify_signal as classify_signal_func
from database import SessionLocal, Lead
from config import Settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


# ============================================================================
# Task Functions
# ============================================================================

async def scheduled_job_board_poll():
    """
    Scheduled task to poll job boards for new marketing roles.
    Runs daily at 9 AM.
    """
    logger.info("Starting scheduled job board poll...")

    db = SessionLocal()
    try:
        # Initialize job board API client
        client = JobBoardAPIClient()

        # Fetch jobs from all configured boards
        jobs = await client.fetch_all_marketing_jobs(
            boards=["naukri", "linkedin"],
            keywords=["marketing manager", "growth hacker", "digital marketing", "marketing head"],
            location="India",
            max_results_per_board=25
        )

        logger.info(f"Fetched {len(jobs)} jobs from job boards")

        # Classify each job
        created_leads = []
        for job in jobs:
            try:
                # Convert job to signal text
                signal_text = job_to_signal_text(job)

                # Create signal input
                signal = SignalInput(
                    signal_text=signal_text,
                    source_type="job_post",
                    company_name=job.company_name,
                    source_url=job.url,
                )

                # Classify (no background tasks in scheduled context)
                result = await classify_signal_func(signal, background_tasks=None, db=db)

                if result.total_score >= 40:  # Only track if at least "nurture" quality
                    created_leads.append({
                        "company": job.company_name,
                        "title": job.title,
                        "score": result.total_score,
                        "bucket": result.score_bucket,
                    })

            except Exception as e:
                logger.error(f"Error classifying job from {job.company_name}: {e}")

        logger.info(f"Scheduled job poll complete. Created {len(created_leads)} leads.")

        # Optionally: Send summary email/notification here
        return {
            "total_jobs_fetched": len(jobs),
            "leads_created": len(created_leads),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in scheduled job board poll: {e}")
        return {"error": str(e)}

    finally:
        db.close()


async def scheduled_rss_feed_monitor():
    """
    Scheduled task to monitor configured RSS feeds.
    Runs every 6 hours.
    """
    logger.info("Starting scheduled RSS feed monitor...")

    # TODO: Store RSS feed URLs in database or config
    # For now, this is a placeholder

    rss_feeds = [
        # Add your RSS feed URLs here
        # "https://example.com/jobs/feed.xml",
    ]

    if not rss_feeds:
        logger.info("No RSS feeds configured for monitoring")
        return {"message": "No feeds configured"}

    try:
        import feedparser

        db = SessionLocal()
        total_items_processed = 0

        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # Process max 10 items per feed
                    title = entry.get("title", "")
                    description = entry.get("description", "") or entry.get("summary", "")
                    link = entry.get("link", "")

                    if not description:
                        continue

                    # Build signal text
                    signal_text = f"Title: {title}\n\nDescription: {description}"

                    # Classify
                    signal = SignalInput(
                        signal_text=signal_text,
                        source_type="rss_feed",
                        source_url=link,
                    )

                    result = await classify_signal_func(signal, background_tasks=None, db=db)

                    if result.total_score >= 40:
                        total_items_processed += 1

            except Exception as e:
                logger.error(f"Error processing RSS feed {feed_url}: {e}")

        logger.info(f"RSS feed monitor complete. Processed {total_items_processed} items.")

        db.close()
        return {
            "feeds_monitored": len(rss_feeds),
            "items_processed": total_items_processed,
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError:
        logger.error("feedparser not installed. Cannot monitor RSS feeds.")
        return {"error": "feedparser not installed"}

    except Exception as e:
        logger.error(f"Error in scheduled RSS feed monitor: {e}")
        return {"error": str(e)}


async def scheduled_auto_park_leads():
    """
    Scheduled task to auto-park old leads that haven't been contacted.
    Runs daily at 2:00 AM.
    """
    logger.info("Starting scheduled auto-park of old leads...")

    settings = Settings()

    if not settings.enable_auto_park:
        logger.info("Auto-park is disabled in configuration")
        return {"message": "Auto-park disabled"}

    db = SessionLocal()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=settings.auto_park_days)

        # Find leads to park
        leads_to_park = db.query(Lead).filter(
            Lead.status == "new",
            Lead.created_at < cutoff_date,
            Lead.auto_parked_at.is_(None)
        ).all()

        parked_count = 0
        for lead in leads_to_park:
            lead.status = "parked"
            lead.auto_parked_at = datetime.utcnow()
            lead.notes = (lead.notes or "") + f"\n[Auto-parked on {datetime.utcnow().date()} - no contact for {settings.auto_park_days} days]"
            db.add(lead)
            parked_count += 1

        db.commit()

        logger.info(f"✅ Auto-parked {parked_count} leads older than {settings.auto_park_days} days")

        return {
            "parked_count": parked_count,
            "cutoff_date": cutoff_date.isoformat(),
            "auto_park_days": settings.auto_park_days,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in scheduled auto-park: {e}")
        return {"error": str(e)}

    finally:
        db.close()


# ============================================================================
# Scheduler Configuration
# ============================================================================

def configure_scheduler():
    """
    Configure and add all scheduled tasks to the scheduler.
    """
    # Job board poll - Daily at 9:00 AM
    scheduler.add_job(
        scheduled_job_board_poll,
        trigger=CronTrigger(hour=9, minute=0),
        id="job_board_poll",
        name="Daily Job Board Poll",
        replace_existing=True,
    )
    logger.info("Scheduled: Daily Job Board Poll at 9:00 AM")

    # RSS feed monitor - Every 6 hours
    scheduler.add_job(
        scheduled_rss_feed_monitor,
        trigger=IntervalTrigger(hours=6),
        id="rss_feed_monitor",
        name="RSS Feed Monitor",
        replace_existing=True,
    )
    logger.info("Scheduled: RSS Feed Monitor every 6 hours")

    # Auto-park old leads - Daily at 2:00 AM
    settings = Settings()
    if settings.enable_auto_park:
        scheduler.add_job(
            scheduled_auto_park_leads,
            trigger=CronTrigger(hour=2, minute=0),
            id="auto_park_leads",
            name="Auto-Park Old Leads",
            replace_existing=True,
        )
        logger.info(f"Scheduled: Auto-Park Old Leads at 2:00 AM (park after {settings.auto_park_days} days)")

    # Add more scheduled tasks here as needed
    # Examples:
    # - Company website re-scraping (weekly)
    # - Lead score recalculation (daily)
    # - Data cleanup (weekly)


def start_scheduler():
    """
    Start the scheduler.
    Call this from main.py on application startup.
    """
    if not scheduler.running:
        configure_scheduler()
        scheduler.start()
        logger.info("Scheduler started successfully")
    else:
        logger.warning("Scheduler is already running")


def stop_scheduler():
    """
    Stop the scheduler.
    Call this on application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def get_scheduled_jobs():
    """
    Get list of all scheduled jobs with their next run times.

    Returns:
        List of job information dictionaries
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs


def trigger_job_now(job_id: str):
    """
    Manually trigger a scheduled job to run immediately.

    Args:
        job_id: The ID of the job to trigger
    """
    job = scheduler.get_job(job_id)
    if job:
        job.modify(next_run_time=datetime.now())
        logger.info(f"Manually triggered job: {job_id}")
        return True
    else:
        logger.error(f"Job not found: {job_id}")
        return False
