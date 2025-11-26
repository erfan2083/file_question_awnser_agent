"""
RAG service port (interface).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class RAGService(ABC):
    """Service interface for RAG (Retrieval-Augmented Generation) operations."""

    @abstractmethod
    def process_query(
        self, query: str, chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.

        Args:
            query: User's question
            chat_history: Previous conversation messages

        Returns:
            Dictionary containing:
                - answer: Generated answer
                - citations: List of source citations
                - metadata: Additional metadata
                - error: Error message if any

        Raises:
            RetrievalError: If retrieval fails
            LLMError: If generation fails
        """
        pass
