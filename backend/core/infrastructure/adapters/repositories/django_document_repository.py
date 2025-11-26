"""
Django ORM implementation of DocumentRepository.
"""
from typing import Optional, List
from datetime import datetime

from core.domain.entities.document import Document as DocumentEntity
from core.domain.value_objects.document_status import DocumentStatus
from core.domain.value_objects.file_type import FileType
from core.application.ports.repositories.document_repository import DocumentRepository
from core.infrastructure.persistence.models import Document as DocumentModel


class DjangoDocumentRepository(DocumentRepository):
    """Django ORM implementation of document repository."""

    def save(self, document: DocumentEntity) -> DocumentEntity:
        """Save a document."""
        model = DocumentModel(
            title=document.title,
            file_path=document.file_path,
            file_type=document.file_type.value,
            file_size=document.file_size,
            status=document.status.value,
            language=document.language,
            error_message=document.error_message,
            num_chunks=document.num_chunks,
            num_pages=document.num_pages
        )
        model.save()

        return self._to_entity(model)

    def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        """Get document by ID."""
        try:
            model = DocumentModel.objects.get(id=document_id)
            return self._to_entity(model)
        except DocumentModel.DoesNotExist:
            return None

    def list_all(self) -> List[DocumentEntity]:
        """List all documents."""
        models = DocumentModel.objects.all()
        return [self._to_entity(model) for model in models]

    def list_ready_documents(self) -> List[DocumentEntity]:
        """List all ready documents."""
        models = DocumentModel.objects.filter(status=DocumentStatus.READY.value)
        return [self._to_entity(model) for model in models]

    def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update an existing document."""
        try:
            model = DocumentModel.objects.get(id=document.id)
            model.title = document.title
            model.file_path = document.file_path
            model.file_type = document.file_type.value
            model.file_size = document.file_size
            model.status = document.status.value
            model.language = document.language
            model.error_message = document.error_message
            model.num_chunks = document.num_chunks
            model.num_pages = document.num_pages
            model.processed_at = document.processed_at
            model.save()
            return self._to_entity(model)
        except DocumentModel.DoesNotExist:
            return None

    def delete(self, document_id: int) -> bool:
        """Delete a document."""
        try:
            model = DocumentModel.objects.get(id=document_id)
            model.delete()
            return True
        except DocumentModel.DoesNotExist:
            return False

    def _to_entity(self, model: DocumentModel) -> DocumentEntity:
        """Convert Django model to domain entity."""
        return DocumentEntity(
            id=model.id,
            title=model.title,
            file_path=str(model.file_path),
            file_type=FileType(model.file_type),
            file_size=model.file_size,
            status=DocumentStatus(model.status),
            language=model.language,
            error_message=model.error_message,
            num_chunks=model.num_chunks,
            num_pages=model.num_pages,
            created_at=model.created_at,
            updated_at=model.updated_at,
            processed_at=model.processed_at
        )
