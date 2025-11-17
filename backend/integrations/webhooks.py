"""
Webhook System for Integrations
Allows sending lead data to external services (CRM, Slack, email, etc.)
"""
import logging
import requests
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session
from ..database import Lead, SessionLocal

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event types"""
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_HOT = "lead.hot"  # Score >= 80
    LEAD_STATUS_CHANGED = "lead.status_changed"
    COMPANY_ENRICHED = "company.enriched"
    SCRAPING_COMPLETED = "scraping.completed"


class WebhookManager:
    """
    Manage webhooks for external integrations
    """

    def __init__(self):
        self.webhooks = {}
        self.webhook_history = []

    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        events: List[WebhookEvent],
        headers: Optional[Dict[str, str]] = None,
        secret: Optional[str] = None
    ):
        """
        Register a webhook endpoint

        Args:
            webhook_id: Unique identifier for this webhook
            url: URL to send webhooks to
            events: List of events to trigger on
            headers: Optional custom headers
            secret: Optional secret for signature verification
        """
        self.webhooks[webhook_id] = {
            "url": url,
            "events": events,
            "headers": headers or {},
            "secret": secret,
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        logger.info(f"Registered webhook: {webhook_id} for events: {events}")

    def unregister_webhook(self, webhook_id: str):
        """Remove a webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")

    def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        async_mode: bool = True
    ):
        """
        Trigger webhook event

        Args:
            event: Event type
            data: Event data
            async_mode: If True, send webhooks asynchronously (non-blocking)
        """
        # Find webhooks subscribed to this event
        relevant_webhooks = {
            wh_id: wh_data
            for wh_id, wh_data in self.webhooks.items()
            if event in wh_data["events"] and wh_data["enabled"]
        }

        if not relevant_webhooks:
            return

        payload = {
            "event": event.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Send to each webhook
        for webhook_id, webhook_data in relevant_webhooks.items():
            if async_mode:
                # In production, use Celery or similar for true async
                self._send_webhook(webhook_id, webhook_data, payload)
            else:
                self._send_webhook(webhook_id, webhook_data, payload)

    def _send_webhook(self, webhook_id: str, webhook_data: Dict, payload: Dict):
        """Send webhook HTTP request"""
        try:
            url = webhook_data["url"]
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": payload["event"],
                **webhook_data.get("headers", {})
            }

            # Add signature if secret provided
            if webhook_data.get("secret"):
                import hmac
                import hashlib

                signature = hmac.new(
                    webhook_data["secret"].encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = signature

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            # Log delivery
            self._log_webhook_delivery(
                webhook_id=webhook_id,
                event=payload["event"],
                status_code=response.status_code,
                success=response.ok
            )

            if not response.ok:
                logger.warning(
                    f"Webhook {webhook_id} failed: {response.status_code} - {response.text[:200]}"
                )

        except Exception as e:
            logger.error(f"Error sending webhook {webhook_id}: {e}")
            self._log_webhook_delivery(
                webhook_id=webhook_id,
                event=payload["event"],
                status_code=None,
                success=False,
                error=str(e)
            )

    def _log_webhook_delivery(
        self,
        webhook_id: str,
        event: str,
        status_code: Optional[int],
        success: bool,
        error: Optional[str] = None
    ):
        """Log webhook delivery"""
        log_entry = {
            "webhook_id": webhook_id,
            "event": event,
            "status_code": status_code,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.webhook_history.append(log_entry)

        # Keep only last 500 entries
        if len(self.webhook_history) > 500:
            self.webhook_history = self.webhook_history[-500:]

    def get_webhook_history(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history"""
        history = self.webhook_history[-limit:]
        if webhook_id:
            history = [h for h in history if h["webhook_id"] == webhook_id]
        return history

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks"""
        return [
            {"id": wh_id, **wh_data}
            for wh_id, wh_data in self.webhooks.items()
        ]

    # Pre-built integrations

    def add_slack_webhook(
        self,
        webhook_url: str,
        events: Optional[List[WebhookEvent]] = None
    ):
        """
        Add Slack webhook for lead notifications

        Args:
            webhook_url: Slack incoming webhook URL
            events: Events to notify about (default: hot leads only)
        """
        if events is None:
            events = [WebhookEvent.LEAD_HOT, WebhookEvent.LEAD_CREATED]

        # Wrap Slack URL in formatter
        def send_to_slack(event: WebhookEvent, data: Dict):
            slack_message = self._format_slack_message(event, data)
            try:
                requests.post(webhook_url, json=slack_message, timeout=10)
            except Exception as e:
                logger.error(f"Error sending to Slack: {e}")

        self.register_webhook(
            webhook_id="slack",
            url=webhook_url,
            events=events
        )

    def _format_slack_message(self, event: WebhookEvent, data: Dict) -> Dict:
        """Format data for Slack"""
        if event == WebhookEvent.LEAD_HOT or event == WebhookEvent.LEAD_CREATED:
            lead_data = data.get("lead", {})
            company = lead_data.get("company_name", "Unknown")
            score = lead_data.get("total_score", 0)
            pain = lead_data.get("key_pain", "N/A")

            emoji = "🔥" if score >= 80 else "🎯"

            return {
                "text": f"{emoji} New Hot Lead: {company}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{emoji} New Lead: {company}*\n"
                                    f"*Score:* {score}\n"
                                    f"*Key Pain:* {pain}\n"
                                    f"*Website:* {lead_data.get('website', 'N/A')}"
                        }
                    }
                ]
            }

        return {"text": f"Event: {event.value}"}

    def add_zapier_webhook(
        self,
        webhook_url: str,
        events: Optional[List[WebhookEvent]] = None
    ):
        """
        Add Zapier webhook

        Args:
            webhook_url: Zapier webhook URL
            events: Events to send to Zapier
        """
        if events is None:
            events = [WebhookEvent.LEAD_CREATED, WebhookEvent.LEAD_HOT]

        self.register_webhook(
            webhook_id="zapier",
            url=webhook_url,
            events=events
        )

    def add_custom_crm_webhook(
        self,
        webhook_id: str,
        webhook_url: str,
        api_key: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None
    ):
        """
        Add custom CRM webhook

        Args:
            webhook_id: Identifier for this CRM
            webhook_url: CRM webhook URL
            api_key: Optional API key
            events: Events to send
        """
        if events is None:
            events = [WebhookEvent.LEAD_CREATED]

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.register_webhook(
            webhook_id=webhook_id,
            url=webhook_url,
            events=events,
            headers=headers
        )


# Webhook event triggers (helper functions)

def trigger_lead_created(lead: Lead, webhook_manager: WebhookManager):
    """Trigger webhook when lead is created"""
    data = {
        "lead": {
            "id": lead.id,
            "company_name": lead.company.name if lead.company else None,
            "website": lead.company.website if lead.company else None,
            "total_score": lead.total_score,
            "score_bucket": lead.score_bucket,
            "key_pain": lead.key_pain,
            "economic_buyer": lead.economic_buyer_guess
        }
    }

    webhook_manager.trigger_event(WebhookEvent.LEAD_CREATED, data)

    # Also trigger hot lead event if score >= 80
    if lead.total_score and lead.total_score >= 80:
        webhook_manager.trigger_event(WebhookEvent.LEAD_HOT, data)


def trigger_lead_updated(lead: Lead, webhook_manager: WebhookManager):
    """Trigger webhook when lead is updated"""
    data = {
        "lead": {
            "id": lead.id,
            "company_name": lead.company.name if lead.company else None,
            "total_score": lead.total_score,
            "status": lead.status
        }
    }

    webhook_manager.trigger_event(WebhookEvent.LEAD_UPDATED, data)


def trigger_scraping_completed(results: Dict, webhook_manager: WebhookManager):
    """Trigger webhook when scraping job completes"""
    webhook_manager.trigger_event(WebhookEvent.SCRAPING_COMPLETED, results)


# Global instance
webhook_manager = WebhookManager()
