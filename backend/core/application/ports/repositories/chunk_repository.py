"""
Chunk repository port (interface).
"""
from abc import ABC, abstractmethod
from typing import List

from core.domain.entities.chunk import DocumentChunk


class ChunkRepository(ABC):
    """Repository interface for document chunk persistence."""

    @abstractmethod
    def save_bulk(self, chunks: List[DocumentChunk]) -> None:
        """
        Save multiple chunks in bulk.

        Args:
            chunks: List of document chunks to save
        """
        pass

    @abstractmethod
    def get_chunks_by_document(self, document_id: int) -> List[DocumentChunk]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of document chunks
        """
        pass

    @abstractmethod
    def get_all_chunks_from_ready_documents(self) -> List[DocumentChunk]:
        """
        Get all chunks from ready documents.

        Returns:
            List of all chunks from ready documents
        """
        pass

    @abstractmethod
    def delete_by_document(self, document_id: int) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document identifier
        """
        pass

    @abstractmethod
    def count_by_document(self, document_id: int) -> int:
        """
        Count chunks for a document.

        Args:
            document_id: Document identifier

        Returns:
            Number of chunks
        """
        pass
