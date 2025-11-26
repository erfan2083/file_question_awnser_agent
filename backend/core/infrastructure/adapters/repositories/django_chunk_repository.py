"""
Django ORM implementation of ChunkRepository.
"""
from typing import List

from core.domain.entities.chunk import DocumentChunk as ChunkEntity
from core.domain.value_objects.embedding import Embedding
from core.application.ports.repositories.chunk_repository import ChunkRepository
from core.infrastructure.persistence.models import DocumentChunk as ChunkModel, Document


class DjangoChunkRepository(ChunkRepository):
    """Django ORM implementation of chunk repository."""

    def save_bulk(self, chunks: List[ChunkEntity]) -> None:
        """Save multiple chunks in bulk."""
        chunk_models = []
        for chunk in chunks:
            model = ChunkModel(
                document_id=chunk.document_id,
                index=chunk.index,
                text=chunk.text,
                embedding=chunk.embedding.vector,
                page_number=chunk.page_number,
                char_count=chunk.char_count,
                token_count=chunk.token_count
            )
            chunk_models.append(model)

        ChunkModel.objects.bulk_create(chunk_models)

    def get_chunks_by_document(self, document_id: int) -> List[ChunkEntity]:
        """Get all chunks for a document."""
        models = ChunkModel.objects.filter(document_id=document_id).order_by('index')
        return [self._to_entity(model) for model in models]

    def get_all_chunks_from_ready_documents(self) -> List[ChunkEntity]:
        """Get all chunks from ready documents."""
        models = ChunkModel.objects.filter(
            document__status='READY'
        ).select_related('document')
        return [self._to_entity(model) for model in models]

    def delete_by_document(self, document_id: int) -> None:
        """Delete all chunks for a document."""
        ChunkModel.objects.filter(document_id=document_id).delete()

    def count_by_document(self, document_id: int) -> int:
        """Count chunks for a document."""
        return ChunkModel.objects.filter(document_id=document_id).count()

    def _to_entity(self, model: ChunkModel) -> ChunkEntity:
        """Convert Django model to domain entity."""
        return ChunkEntity(
            id=model.id,
            document_id=model.document_id,
            index=model.index,
            text=model.text,
            embedding=Embedding(model.embedding),
            page_number=model.page_number,
            char_count=model.char_count,
            token_count=model.token_count
        )
