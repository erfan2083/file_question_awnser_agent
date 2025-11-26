"""
PDF text extractor implementation.
"""
from typing import Tuple

import PyPDF2
import pdfplumber

from core.domain.value_objects.file_type import FileType
from core.domain.exceptions import TextExtractionError
from core.application.ports.services.text_extractor import TextExtractor


class PDFTextExtractor(TextExtractor):
    """PDF text extraction implementation."""

    def can_extract(self, file_type: FileType) -> bool:
        """Check if this extractor can handle PDF files."""
        return file_type == FileType.PDF

    def extract(self, file_path: str) -> Tuple[str, int]:
        """Extract text from PDF file."""
        text_parts = []
        num_pages = 0

        try:
            # Try pdfplumber first (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                num_pages = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    num_pages = len(pdf_reader.pages)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except Exception as fallback_error:
                raise TextExtractionError(f"Failed to extract PDF text: {fallback_error}")

        return "\n\n".join(text_parts), num_pages
