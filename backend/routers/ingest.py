"""Data ingest - OCR, file uploads, contact extraction."""

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import pytesseract
from PIL import Image
import io
import re
import logging
import csv
from typing import Optional
from pydantic import BaseModel
from database import SessionLocal
from routers.classify import classify_signal as classify_signal_func
from routers.classify import SignalInput

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OCRResult(BaseModel):
    extracted_text: str
    detected_emails: list
    detected_phones: list
    detected_names: list
    detected_company: Optional[str]

def extract_emails(text: str) -> list:
    """Extract email addresses from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_phones(text: str) -> list:
    """Extract phone numbers from text using regex."""
    phone_patterns = [
        r'\+91[-.\s]?\d{10}',  # +91 followed by 10 digits
        r'91[-.\s]?\d{10}',  # 91 followed by 10 digits
        r'\b\d{10}\b',  # 10 consecutive digits
        r'[6-9]\d{9}',  # Indian phone starting with 6-9
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))  # Remove duplicates

def extract_names(text: str) -> list:
    """Simple name extraction - look for capitalized word sequences."""
    # Very basic: find sequences of capitalized words
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    return re.findall(name_pattern, text)[:5]  # Return max 5

def extract_company(text: str) -> Optional[str]:
    """Try to extract company name from text."""
    # Look for common patterns: "Company:", "at X", "X Ltd", "X Pvt Ltd"
    patterns = [
        r'(?:Company|company|business|firm|organization)\s*:?\s*([A-Za-z0-9\s&.,]+)',
        r'at\s+([A-Za-z0-9\s&]+?)(?:\s+[,.]|$)',
        r'([A-Za-z0-9\s&]+?)\s+(?:Pvt|Ltd|Inc|Corporation|Services)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None

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
        if file.content_type.startswith("image"):
            # Image handling: use Tesseract OCR
            image = Image.open(io.BytesIO(contents))
            extracted_text = pytesseract.image_to_string(image, lang='eng')
            logger.info(f"OCR'd image: {file.filename}")
        elif file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            # PDF handling: extract text directly using pypdf
            if PdfReader is None:
                raise HTTPException(status_code=500, detail="PDF support not available. Install pypdf: pip install pypdf")

            try:
                pdf_file = io.BytesIO(contents)
                reader = PdfReader(pdf_file)
                pages_text = []
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                extracted_text = "\n".join(pages_text)
                logger.info(f"Extracted text from {len(reader.pages)} pages of {file.filename}")
            except Exception as pdf_err:
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(pdf_err)}")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use image (.jpg, .png, .gif) or PDF.")

        # Clean up extracted text
        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from file")

        # Extract contact info
        emails = extract_emails(extracted_text)
        phones = extract_phones(extracted_text)
        names = extract_names(extracted_text)
        company = extract_company(extracted_text)

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
):
    """
    Upload a file (image or PDF), extract text, and immediately classify as a lead.
    If score > threshold, queue dossier generation (background task).
    """
    try:
        # Step 1: Extract text
        contents = await file.read()

        if file.content_type.startswith("image"):
            # Image: OCR with Tesseract
            image = Image.open(io.BytesIO(contents))
            extracted_text = pytesseract.image_to_string(image, lang='eng')
            source_type = "ocr_image"
        elif file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            # PDF: text extraction
            if PdfReader is None:
                raise HTTPException(status_code=500, detail="PDF support not available. Install: pip install pypdf")

            try:
                pdf_file = io.BytesIO(contents)
                reader = PdfReader(pdf_file)
                pages_text = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                extracted_text = "\n".join(pages_text)
                source_type = "ocr_pdf"
            except Exception as pdf_err:
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(pdf_err)}")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use image or PDF.")

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from file")

        # Step 2: Classify
        signal = SignalInput(
            signal_text=extracted_text,
            source_type=source_type,
            company_name=company_name or extract_company(extracted_text),
        )

        result = await classify_signal_func(signal, background_tasks, db)
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

            # Classify synchronously (for CSV, we do batch processing)
            try:
                result = await classify_signal_func(signal, background_tasks, db)
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
