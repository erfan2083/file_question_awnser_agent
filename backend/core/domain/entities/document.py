"""
Document entity - core domain model.
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

from core.domain.value_objects.document_status import DocumentStatus
from core.domain.value_objects.file_type import FileType
from core.domain.exceptions import InvalidDocumentStateError


@dataclass
class Document:
    """
    Document entity representing an uploaded document.

    This is a pure domain entity with business logic.
    """

    id: Optional[int]
    title: str
    file_path: str
    file_type: FileType
    file_size: int
    status: DocumentStatus = DocumentStatus.UPLOADED
    language: Optional[str] = None
    error_message: Optional[str] = None
    num_chunks: int = 0
    num_pages: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    def start_processing(self) -> None:
        """Mark document as processing."""
        if not self.status.can_transition_to(DocumentStatus.PROCESSING):
            raise InvalidDocumentStateError(
                f"Cannot transition from {self.status} to PROCESSING"
            )
        self.status = DocumentStatus.PROCESSING
        self.error_message = None

    def mark_as_ready(self, num_chunks: int, num_pages: int) -> None:
        """Mark document as ready after successful processing."""
        if not self.status.can_transition_to(DocumentStatus.READY):
            raise InvalidDocumentStateError(
                f"Cannot transition from {self.status} to READY"
            )
        self.status = DocumentStatus.READY
        self.num_chunks = num_chunks
        self.num_pages = num_pages
        self.processed_at = datetime.now()
        self.error_message = None

    def mark_as_failed(self, error_message: str) -> None:
        """Mark document as failed with error message."""
        if not self.status.can_transition_to(DocumentStatus.FAILED):
            raise InvalidDocumentStateError(
                f"Cannot transition from {self.status} to FAILED"
            )
        self.status = DocumentStatus.FAILED
        self.error_message = error_message

    def is_ready(self) -> bool:
        """Check if document is ready for querying."""
        return self.status == DocumentStatus.READY

    def is_processing(self) -> bool:
        """Check if document is being processed."""
        return self.status == DocumentStatus.PROCESSING

    def is_failed(self) -> bool:
        """Check if document processing failed."""
        return self.status == DocumentStatus.FAILED

    def __repr__(self):
        return f"Document(id={self.id}, title='{self.title}', status={self.status})"
