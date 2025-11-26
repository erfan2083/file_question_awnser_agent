"""
Text extractor service port (interface).
"""
from abc import ABC, abstractmethod
from typing import Tuple

from core.domain.value_objects.file_type import FileType


class TextExtractor(ABC):
    """Service interface for extracting text from documents."""

    @abstractmethod
    def can_extract(self, file_type: FileType) -> bool:
        """
        Check if this extractor can handle the given file type.

        Args:
            file_type: Type of file

        Returns:
            True if can extract, False otherwise
        """
        pass

    @abstractmethod
    def extract(self, file_path: str) -> Tuple[str, int]:
        """
        Extract text from file.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (extracted_text, num_pages)

        Raises:
            TextExtractionError: If extraction fails
        """
        pass
