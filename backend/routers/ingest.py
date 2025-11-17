"""Data ingest - OCR, file uploads, contact extraction."""

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import logging
import csv
from typing import Optional

from dependencies import get_db, get_settings
from schemas.ingest import OCRResult
from schemas.classification import SignalInput
from services.ingest_service import IngestService
from services.classification_service import ClassificationService
from config import Settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ocr", response_model=OCRResult)
async def ingest_ocr(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an image or PDF and extract text.
    For images: use Tesseract OCR.
    For PDFs: extract text directly (faster, no rasterization).
    Also extract contact info (emails, phones, names, company).
    """
    try:
        # Read file
        contents = await file.read()

        # Extract text based on file type
        if file.content_type and file.content_type.startswith("image"):
            extracted_text = IngestService.extract_text_from_image(contents)
            logger.info(f"OCR'd image: {file.filename}")
        elif file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            try:
                extracted_text = IngestService.extract_text_from_pdf(contents)
                logger.info(f"Extracted text from PDF: {file.filename}")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use image (.jpg, .png, .gif) or PDF."
            )

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from file")

        # Extract contact info
        emails = IngestService.extract_emails(extracted_text)
        phones = IngestService.extract_phones(extracted_text)
        names = IngestService.extract_names(extracted_text)
        company = IngestService.extract_company(extracted_text)

        return OCRResult(
            extracted_text=extracted_text,
            detected_emails=emails,
            detected_phones=phones,
            detected_names=names,
            detected_company=company,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OCR ingest: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/ocr-and-classify")
async def ingest_ocr_and_classify(
    file: UploadFile = File(...),
    company_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a file (image or PDF), extract text, and immediately classify as a lead.
    If score > threshold, queue dossier generation (background task).
    """
    try:
        # Step 1: Extract text
        contents = await file.read()

        if file.content_type and file.content_type.startswith("image"):
            extracted_text = IngestService.extract_text_from_image(contents)
            source_type = "ocr_image"
        elif file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            try:
                extracted_text = IngestService.extract_text_from_pdf(contents)
                source_type = "ocr_pdf"
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use image or PDF."
            )

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from file")

        # Step 2: Classify
        signal = SignalInput(
            signal_text=extracted_text,
            source_type=source_type,
            company_name=company_name or IngestService.extract_company(extracted_text),
        )

        result = await ClassificationService.classify_signal(db, signal, settings)

        # Queue dossier generation if needed
        if ClassificationService.should_generate_dossier(result.total_score, settings):
            lead_json = {
                "role_type": result.classification.get("role_type"),
                "company_name": signal.company_name,
                "pain_tags": result.classification.get("pain_tags", []),
                "situation": result.classification.get("situation", ""),
                "problem": result.classification.get("problem", ""),
            }
            signal_snippets = [extracted_text[:500]]

            if background_tasks:
                background_tasks.add_task(
                    ClassificationService.generate_dossier_async,
                    result.lead_id,
                    lead_json,
                    signal_snippets,
                    db,
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OCR classify: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Bulk ingest from CSV and classify each signal.
    Expected columns: company_name, company_website (optional), signal_text

    Returns summary of created leads.
    """
    try:
        import io as stdio

        contents = await file.read()
        stream = stdio.StringIO(contents.decode("utf8"))
        csv_reader = csv.DictReader(stream)

        results = []
        processed_count = 0

        for row in csv_reader:
            signal_text = row.get("signal_text", "").strip()
            company_name = row.get("company_name", "").strip()

            if not signal_text:
                continue  # Skip empty rows

            processed_count += 1

            # Create signal input
            signal = SignalInput(
                signal_text=signal_text,
                source_type="csv",
                company_name=company_name or None,
                company_website=row.get("company_website") or None,
            )

            # Classify
            try:
                result = await ClassificationService.classify_signal(db, signal, settings)
                results.append({
                    "company": company_name,
                    "score": result.total_score,
                    "bucket": result.score_bucket,
                    "lead_id": result.lead_id,
                    "status": "created",
                })
            except Exception as e:
                logger.error(f"Error classifying CSV row {processed_count}: {e}")
                results.append({
                    "company": company_name,
                    "status": "error",
                    "error": str(e),
                })

        return {
            "total_processed": processed_count,
            "total_created": len([r for r in results if r.get("status") == "created"]),
            "results": results,
            "message": f"Processed {processed_count} rows, created {len([r for r in results if r.get('status') == 'created'])} leads",
        }

    except Exception as e:
        logger.error(f"Error in CSV ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))
