"""
Enrichment API Endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import logging
from io import BytesIO

from ..enrichment.contact_finder import contact_finder
from ..enrichment.company_enrichment import company_enrichment
from ..export.exporters import lead_exporter
from ..automation.scheduler import job_scheduler
from ..integrations.webhooks import webhook_manager, WebhookEvent
from ..database import SessionLocal, Lead, Company

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


# Contact Finding

class ContactFindRequest(BaseModel):
    company_name: str
    website: Optional[HttpUrl] = None
    person_name: Optional[str] = None


@router.post("/find-contacts", summary="Find contact information")
async def find_contacts(request: ContactFindRequest) -> Dict[str, Any]:
    """
    Find contact emails and phones for a company/person

    Generates email patterns, scrapes websites, and verifies deliverability
    """
    try:
        candidates = contact_finder.find_contacts(
            company_name=request.company_name,
            website=str(request.website) if request.website else None,
            person_name=request.person_name
        )

        return {
            "company_name": request.company_name,
            "total_candidates": len(candidates),
            "candidates": [
                {
                    "email": c.email,
                    "pattern": c.pattern,
                    "confidence": c.confidence,
                    "deliverable": c.deliverable,
                    "source": c.source
                }
                for c in candidates[:20]  # Return top 20
            ]
        }

    except Exception as e:
        logger.error(f"Error finding contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Company Enrichment

class CompanyEnrichRequest(BaseModel):
    company_name: str
    website: Optional[HttpUrl] = None
    deep: Optional[bool] = False


@router.post("/enrich-company", summary="Enrich company data")
async def enrich_company(request: CompanyEnrichRequest) -> Dict[str, Any]:
    """
    Enrich company with comprehensive intelligence

    Gathers data from multiple sources:
    - Company website
    - Tech stack detection
    - Social profiles
    - Funding data (if available)
    - Hiring velocity
    - Intent signals
    """
    try:
        enrichment = company_enrichment.enrich_company(
            company_name=request.company_name,
            website=str(request.website) if request.website else None,
            deep=request.deep or False
        )

        return {
            "success": True,
            "enrichment": enrichment
        }

    except Exception as e:
        logger.error(f"Error enriching company: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich-lead/{lead_id}", summary="Enrich a specific lead")
async def enrich_lead(lead_id: int, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Enrich a specific lead with company and contact data
    """
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        company = lead.company
        if not company:
            raise HTTPException(status_code=400, detail="Lead has no associated company")

        # Enrich company
        if company.website:
            enrichment = company_enrichment.enrich_company(
                company_name=company.name,
                website=company.website,
                deep=True
            )

            # Update company
            if enrichment.get("description"):
                company.description = enrichment["description"]

            if not company.metadata:
                company.metadata = {}

            company.metadata["enrichment"] = enrichment
            db.commit()

        # Find contacts
        if company.website:
            candidates = contact_finder.find_contacts(
                company_name=company.name,
                website=company.website
            )

            if not company.metadata:
                company.metadata = {}

            company.metadata["email_candidates"] = [
                {"email": c.email, "confidence": c.confidence, "verified": c.deliverable}
                for c in candidates[:10]
            ]
            db.commit()

        return {
            "success": True,
            "message": f"Enriched lead #{lead_id}",
            "company_enriched": True,
            "contacts_found": len(candidates) if candidates else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enriching lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Batch Enrichment

@router.post("/batch-enrich", summary="Batch enrich all leads")
async def batch_enrich(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = 50
) -> Dict[str, Any]:
    """
    Enrich multiple leads in the background

    This is a long-running operation that enriches leads without complete data
    """
    db = SessionLocal()
    try:
        # Get leads that need enrichment
        leads = db.query(Lead).join(Company).filter(
            (Company.metadata == None) | (Company.website != None)
        ).limit(limit).all()

        def enrich_batch():
            enriched_count = 0
            for lead in leads:
                try:
                    if lead.company and lead.company.website:
                        enrichment = company_enrichment.enrich_company(
                            company_name=lead.company.name,
                            website=lead.company.website,
                            deep=False
                        )

                        if not lead.company.metadata:
                            lead.company.metadata = {}

                        lead.company.metadata["enrichment"] = enrichment
                        enriched_count += 1
                except Exception as e:
                    logger.error(f"Error enriching lead {lead.id}: {e}")

            db.commit()
            logger.info(f"Batch enrichment completed: {enriched_count}/{len(leads)} enriched")

        background_tasks.add_task(enrich_batch)

        return {
            "success": True,
            "message": f"Batch enrichment started for {len(leads)} leads",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error in batch enrichment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Export Endpoints

@router.get("/export/csv", summary="Export leads to CSV")
async def export_csv(
    score_min: Optional[int] = 0,
    score_bucket: Optional[str] = None,
    include_dossier: Optional[bool] = False
):
    """Export leads to CSV format"""
    db = SessionLocal()
    try:
        query = db.query(Lead)

        if score_min:
            query = query.filter(Lead.total_score >= score_min)

        if score_bucket:
            query = query.filter(Lead.score_bucket == score_bucket)

        leads = query.all()

        csv_content = lead_exporter.export_to_csv(leads, include_dossier=include_dossier)

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads.csv"}
        )

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/export/excel", summary="Export leads to Excel")
async def export_excel(
    score_min: Optional[int] = 0,
    score_bucket: Optional[str] = None,
    include_dossier: Optional[bool] = False
):
    """Export leads to Excel format with formatting"""
    db = SessionLocal()
    try:
        query = db.query(Lead)

        if score_min:
            query = query.filter(Lead.total_score >= score_min)

        if score_bucket:
            query = query.filter(Lead.score_bucket == score_bucket)

        leads = query.all()

        excel_file = lead_exporter.export_to_excel(
            leads,
            include_dossier=include_dossier,
            include_summary=True
        )

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
        )

    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/export/json", summary="Export leads to JSON")
async def export_json(
    score_min: Optional[int] = 0,
    score_bucket: Optional[str] = None,
    include_dossier: Optional[bool] = True
):
    """Export leads to JSON format"""
    db = SessionLocal()
    try:
        query = db.query(Lead)

        if score_min:
            query = query.filter(Lead.total_score >= score_min)

        if score_bucket:
            query = query.filter(Lead.score_bucket == score_bucket)

        leads = query.all()

        json_content = lead_exporter.export_to_json(leads, include_dossier=include_dossier)

        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=leads.json"}
        )

    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/export/pdf", summary="Export leads to PDF")
async def export_pdf(
    score_min: Optional[int] = 0,
    score_bucket: Optional[str] = None,
    include_dossier: Optional[bool] = True
):
    """Export leads to PDF report"""
    db = SessionLocal()
    try:
        query = db.query(Lead)

        if score_min:
            query = query.filter(Lead.total_score >= score_min)

        if score_bucket:
            query = query.filter(Lead.score_bucket == score_bucket)

        leads = query.all()

        pdf_file = lead_exporter.export_to_pdf(
            leads,
            include_dossier=include_dossier,
            title="Lead Report"
        )

        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=leads.pdf"}
        )

    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
