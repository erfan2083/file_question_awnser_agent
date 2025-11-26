"""
TXT text extractor implementation.
"""
from typing import Tuple

from core.domain.value_objects.file_type import FileType
from core.domain.exceptions import TextExtractionError
from core.application.ports.services.text_extractor import TextExtractor


class TXTTextExtractor(TextExtractor):
    """TXT text extraction implementation."""

    def can_extract(self, file_type: FileType) -> bool:
        """Check if this extractor can handle TXT files."""
        return file_type == FileType.TXT

    def extract(self, file_path: str) -> Tuple[str, int]:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()

            # Estimate pages (roughly 3000 chars per page)
            num_pages = max(1, len(text) // 3000)
            return text, num_pages
        except Exception as e:
            raise TextExtractionError(f"Failed to extract TXT text: {str(e)}")
