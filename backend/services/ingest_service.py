"""Data ingest business logic service for OCR and file processing."""

import re
import logging
from typing import List, Optional
from PIL import Image
import pytesseract

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)


class IngestService:
    """Service for OCR and data extraction."""

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text using regex.

        Args:
            text: Input text

        Returns:
            List of email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)

    @staticmethod
    def extract_phones(text: str) -> List[str]:
        """
        Extract phone numbers from text using regex.

        Args:
            text: Input text

        Returns:
            List of phone numbers
        """
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

    @staticmethod
    def extract_names(text: str) -> List[str]:
        """
        Simple name extraction - look for capitalized word sequences.

        Args:
            text: Input text

        Returns:
            List of potential names (max 5)
        """
        # Very basic: find sequences of capitalized words
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        return re.findall(name_pattern, text)[:5]

    @staticmethod
    def extract_company(text: str) -> Optional[str]:
        """
        Try to extract company name from text.

        Args:
            text: Input text

        Returns:
            Company name if found
        """
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

    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> str:
        """
        Extract text from image using Tesseract OCR.

        Args:
            image_bytes: Image file bytes

        Returns:
            Extracted text
        """
        import io
        image = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(image, lang='eng')
        return extracted_text.strip()

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_bytes: PDF file bytes

        Returns:
            Extracted text

        Raises:
            ValueError: If pypdf is not installed or PDF parsing fails
        """
        if PdfReader is None:
            raise ValueError("PDF support not available. Install pypdf: pip install pypdf")

        import io
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
