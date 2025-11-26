"""
Use case for uploading a document.
"""
from typing import Optional

from core.domain.entities.document import Document
from core.domain.value_objects.document_status import DocumentStatus
from core.domain.value_objects.file_type import FileType
from core.application.ports.repositories.document_repository import DocumentRepository
from core.application.dto.document_dto import DocumentUploadDTO, DocumentDTO


class UploadDocumentUseCase:
    """Use case for uploading a document."""

    def __init__(self, document_repository: DocumentRepository):
        """
        Initialize use case.

        Args:
            document_repository: Repository for document persistence
        """
        self.document_repository = document_repository

    def execute(self, upload_dto: DocumentUploadDTO) -> DocumentDTO:
        """
        Execute the upload document use case.

        Args:
            upload_dto: Document upload data

        Returns:
            DocumentDTO with created document information

        Raises:
            ValueError: If file type is invalid
        """
        # Validate and create file type
        file_type = FileType(upload_dto.file_type.lower())

        # Create document entity
        document = Document(
            id=None,
            title=upload_dto.title,
            file_path=upload_dto.file_path,
            file_type=file_type,
            file_size=upload_dto.file_size,
            status=DocumentStatus.UPLOADED,
            language=upload_dto.language
        )

        # Save document
        saved_document = self.document_repository.save(document)

        # Convert to DTO
        return self._to_dto(saved_document)

    def _to_dto(self, document: Document) -> DocumentDTO:
        """Convert domain entity to DTO."""
        return DocumentDTO(
            id=document.id,
            title=document.title,
            file_path=document.file_path,
            file_type=document.file_type.value,
            file_size=document.file_size,
            status=document.status.value,
            language=document.language,
            error_message=document.error_message,
            num_chunks=document.num_chunks,
            num_pages=document.num_pages,
            created_at=document.created_at,
            updated_at=document.updated_at,
            processed_at=document.processed_at
        )
