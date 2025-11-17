"""
Automation API Endpoints - Scheduling & Webhooks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import logging

from ..automation.scheduler import job_scheduler
from ..integrations.webhooks import webhook_manager, WebhookEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["automation"])


# Scheduled Jobs

class ScheduleJobScrapeRequest(BaseModel):
    job_id: str
    query: str
    sources: Optional[List[str]] = ["indeed", "naukri"]
    hour: Optional[int] = 9
    minute: Optional[int] = 0


class ScheduleEnrichmentRequest(BaseModel):
    job_id: str
    interval_hours: Optional[int] = 24


class ScheduleDiscoveryRequest(BaseModel):
    job_id: str
    search_queries: List[str]
    interval_hours: Optional[int] = 168  # Weekly


@router.post("/schedule/job-scrape", summary="Schedule daily job scraping")
async def schedule_job_scrape(request: ScheduleJobScrapeRequest) -> Dict[str, Any]:
    """
    Schedule automatic daily job board scraping

    **Example:**
    ```json
    {
        "job_id": "daily_marketing_jobs",
        "query": "marketing manager",
        "sources": ["indeed", "naukri"],
        "hour": 9,
        "minute": 0
    }
    ```
    """
    try:
        job_scheduler.add_daily_job_scrape(
            job_id=request.job_id,
            query=request.query,
            sources=request.sources,
            hour=request.hour,
            minute=request.minute
        )

        return {
            "success": True,
            "message": f"Scheduled daily job scrape: {request.job_id}",
            "schedule": f"Daily at {request.hour:02d}:{request.minute:02d}"
        }

    except Exception as e:
        logger.error(f"Error scheduling job scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/enrichment", summary="Schedule periodic enrichment")
async def schedule_enrichment(request: ScheduleEnrichmentRequest) -> Dict[str, Any]:
    """
    Schedule automatic company enrichment

    Enriches companies that are missing data
    """
    try:
        job_scheduler.add_enrichment_job(
            job_id=request.job_id,
            interval_hours=request.interval_hours
        )

        return {
            "success": True,
            "message": f"Scheduled enrichment job: {request.job_id}",
            "schedule": f"Every {request.interval_hours} hours"
        }

    except Exception as e:
        logger.error(f"Error scheduling enrichment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/discovery", summary="Schedule lead discovery")
async def schedule_discovery(request: ScheduleDiscoveryRequest) -> Dict[str, Any]:
    """
    Schedule automatic lead discovery via search engines

    **Example:**
    ```json
    {
        "job_id": "weekly_saas_discovery",
        "search_queries": [
            "SaaS startup India hiring marketing",
            "D2C ecommerce India growth"
        ],
        "interval_hours": 168
    }
    ```
    """
    try:
        job_scheduler.add_lead_discovery_job(
            job_id=request.job_id,
            search_queries=request.search_queries,
            interval_hours=request.interval_hours
        )

        return {
            "success": True,
            "message": f"Scheduled lead discovery: {request.job_id}",
            "schedule": f"Every {request.interval_hours} hours"
        }

    except Exception as e:
        logger.error(f"Error scheduling lead discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/jobs", summary="List scheduled jobs")
async def list_scheduled_jobs() -> Dict[str, Any]:
    """List all scheduled jobs"""
    try:
        jobs = job_scheduler.list_jobs()
        return {
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/jobs/{job_id}", summary="Remove scheduled job")
async def remove_scheduled_job(job_id: str) -> Dict[str, Any]:
    """Remove a scheduled job"""
    try:
        success = job_scheduler.remove_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "success": True,
            "message": f"Removed job: {job_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/history", summary="Get job execution history")
async def get_job_history(
    job_id: Optional[str] = None,
    limit: Optional[int] = 50
) -> Dict[str, Any]:
    """Get job execution history"""
    try:
        history = job_scheduler.get_job_history(job_id=job_id, limit=limit)
        return {
            "total": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting job history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/start", summary="Start scheduler")
async def start_scheduler() -> Dict[str, str]:
    """Start the job scheduler"""
    try:
        job_scheduler.start()
        return {"status": "started", "message": "Job scheduler started"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/stop", summary="Stop scheduler")
async def stop_scheduler() -> Dict[str, str]:
    """Stop the job scheduler"""
    try:
        job_scheduler.stop()
        return {"status": "stopped", "message": "Job scheduler stopped"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhooks

class RegisterWebhookRequest(BaseModel):
    webhook_id: str
    url: HttpUrl
    events: List[str]
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None


@router.post("/webhooks/register", summary="Register a webhook")
async def register_webhook(request: RegisterWebhookRequest) -> Dict[str, Any]:
    """
    Register a webhook endpoint for events

    **Available Events:**
    - `lead.created` - New lead created
    - `lead.updated` - Lead updated
    - `lead.hot` - Hot lead detected (score >= 80)
    - `lead.status_changed` - Lead status changed
    - `company.enriched` - Company enriched
    - `scraping.completed` - Scraping job completed

    **Example:**
    ```json
    {
        "webhook_id": "my_crm",
        "url": "https://my-crm.com/webhooks/leads",
        "events": ["lead.created", "lead.hot"],
        "headers": {
            "Authorization": "Bearer YOUR_API_KEY"
        },
        "secret": "your_webhook_secret"
    }
    ```
    """
    try:
        # Convert event strings to WebhookEvent enums
        events = [WebhookEvent(e) for e in request.events]

        webhook_manager.register_webhook(
            webhook_id=request.webhook_id,
            url=str(request.url),
            events=events,
            headers=request.headers,
            secret=request.secret
        )

        return {
            "success": True,
            "message": f"Registered webhook: {request.webhook_id}",
            "webhook_id": request.webhook_id,
            "events": request.events
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/webhooks/{webhook_id}", summary="Unregister webhook")
async def unregister_webhook(webhook_id: str) -> Dict[str, str]:
    """Unregister a webhook"""
    try:
        webhook_manager.unregister_webhook(webhook_id)
        return {
            "success": True,
            "message": f"Unregistered webhook: {webhook_id}"
        }
    except Exception as e:
        logger.error(f"Error unregistering webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhooks", summary="List all webhooks")
async def list_webhooks() -> Dict[str, Any]:
    """List all registered webhooks"""
    try:
        webhooks = webhook_manager.list_webhooks()
        return {
            "total": len(webhooks),
            "webhooks": webhooks
        }
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhooks/history", summary="Get webhook delivery history")
async def get_webhook_history(
    webhook_id: Optional[str] = None,
    limit: Optional[int] = 50
) -> Dict[str, Any]:
    """Get webhook delivery history"""
    try:
        history = webhook_manager.get_webhook_history(webhook_id=webhook_id, limit=limit)
        return {
            "total": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting webhook history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pre-built integrations

class SlackWebhookRequest(BaseModel):
    webhook_url: HttpUrl
    events: Optional[List[str]] = ["lead.hot", "lead.created"]


@router.post("/integrations/slack", summary="Add Slack integration")
async def add_slack_integration(request: SlackWebhookRequest) -> Dict[str, str]:
    """
    Add Slack webhook integration

    Get your Slack webhook URL from: https://api.slack.com/messaging/webhooks
    """
    try:
        events = [WebhookEvent(e) for e in request.events]
        webhook_manager.add_slack_webhook(
            webhook_url=str(request.webhook_url),
            events=events
        )

        return {
            "success": True,
            "message": "Slack integration added"
        }
    except Exception as e:
        logger.error(f"Error adding Slack integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ZapierWebhookRequest(BaseModel):
    webhook_url: HttpUrl
    events: Optional[List[str]] = ["lead.created", "lead.hot"]


@router.post("/integrations/zapier", summary="Add Zapier integration")
async def add_zapier_integration(request: ZapierWebhookRequest) -> Dict[str, str]:
    """
    Add Zapier webhook integration

    Create a Zap with a Webhook trigger and paste the URL here
    """
    try:
        events = [WebhookEvent(e) for e in request.events]
        webhook_manager.add_zapier_webhook(
            webhook_url=str(request.webhook_url),
            events=events
        )

        return {
            "success": True,
            "message": "Zapier integration added"
        }
    except Exception as e:
        logger.error(f"Error adding Zapier integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
