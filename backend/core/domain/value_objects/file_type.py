"""
Value object for file types.
"""
from enum import Enum


class FileType(str, Enum):
    """Supported document file types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"

    @classmethod
    def from_filename(cls, filename: str) -> 'FileType':
        """Extract file type from filename."""
        extension = filename.lower().split('.')[-1]
        try:
            return cls(extension)
        except ValueError:
            raise ValueError(f"Unsupported file type: {extension}")

    def is_image(self) -> bool:
        """Check if file type is an image."""
        return self in [self.JPG, self.JPEG, self.PNG]

    def is_document(self) -> bool:
        """Check if file type is a document."""
        return self in [self.PDF, self.DOCX, self.TXT]
