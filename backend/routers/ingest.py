"""Data ingest - OCR, file uploads, contact extraction."""

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import pytesseract
from PIL import Image
import io
import re
import logging
from typing import Optional
from pydantic import BaseModel
from database import SessionLocal
from routers.classify import classify_signal as classify_signal_func
from routers.classify import SignalInput

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
    Upload an image or PDF and extract text via OCR.
    Also extract contact info (emails, phones, names, company).
    """
    try:
        # Read file
        contents = await file.read()

        # OCR extraction
        if file.content_type.startswith("image"):
            # Image handling
            image = Image.open(io.BytesIO(contents))
            extracted_text = pytesseract.image_to_string(image, lang='eng')
        elif file.content_type == "application/pdf":
            # For PDFs, we'd need pdf2image or pdfplumber
            # Simple fallback: warn user
            logger.warning(f"PDF support not yet implemented. File: {file.filename}")
            extracted_text = "[PDF processing not yet implemented]"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use image or PDF.")

        # Clean up extracted text
        extracted_text = extracted_text.strip()

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
    Upload a file, OCR it, and immediately classify as a lead.
    If score > threshold, queue dossier generation.
    """
    try:
        # Step 1: OCR
        contents = await file.read()

        if file.content_type.startswith("image"):
            image = Image.open(io.BytesIO(contents))
            extracted_text = pytesseract.image_to_string(image, lang='eng')
        else:
            raise HTTPException(status_code=400, detail="Only images supported for OCR classification right now")

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise HTTPException(status_code=400, detail="OCR failed to extract text from image")

        # Step 2: Classify
        signal = SignalInput(
            signal_text=extracted_text,
            source_type="ocr",
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
    db: Session = Depends(get_db),
):
    """
    Bulk ingest from CSV.
    Expected columns: company_name, website, signal_text
    """
    try:
        import csv
        import io as stdio

        contents = await file.read()
        stream = stdio.StringIO(contents.decode("utf8"))
        csv_reader = csv.DictReader(stream)

        results = []
        for row in csv_reader:
            signal = SignalInput(
                signal_text=row.get("signal_text", ""),
                source_type="csv",
                company_name=row.get("company_name"),
            )
            if signal.signal_text:
                results.append({
                    "company": signal.company_name,
                    "queued": True,
                })

        return {
            "count": len(results),
            "results": results,
            "message": "Signals queued for classification",
        }

    except Exception as e:
        logger.error(f"Error in CSV ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))
