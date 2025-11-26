"""
Embedding service port (interface).
"""
from abc import ABC, abstractmethod
from typing import List

from core.domain.value_objects.embedding import Embedding


class EmbeddingService(ABC):
    """Service interface for generating embeddings."""

    @abstractmethod
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> Embedding:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            task_type: Type of task (retrieval_document, retrieval_query, etc.)

        Returns:
            Embedding object

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        pass

    @abstractmethod
    def generate_embeddings_batch(
        self, texts: List[str], task_type: str = "retrieval_document"
    ) -> List[Embedding]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            task_type: Type of task

        Returns:
            List of embedding objects

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        pass
