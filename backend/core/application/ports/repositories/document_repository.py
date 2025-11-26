"""
Document repository port (interface).
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from core.domain.entities.document import Document


class DocumentRepository(ABC):
    """Repository interface for document persistence."""

    @abstractmethod
    def save(self, document: Document) -> Document:
        """
        Save a document.

        Args:
            document: Document entity to save

        Returns:
            Saved document with updated fields
        """
        pass

    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[Document]:
        """
        Get document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    def list_all(self) -> List[Document]:
        """
        List all documents.

        Returns:
            List of all documents
        """
        pass

    @abstractmethod
    def list_ready_documents(self) -> List[Document]:
        """
        List all documents that are ready for querying.

        Returns:
            List of ready documents
        """
        pass

    @abstractmethod
    def update(self, document: Document) -> Document:
        """
        Update an existing document.

        Args:
            document: Document entity with updated fields

        Returns:
            Updated document
        """
        pass

    @abstractmethod
    def delete(self, document_id: int) -> bool:
        """
        Delete a document.

        Args:
            document_id: Document identifier

        Returns:
            True if deleted, False otherwise
        """
        pass
