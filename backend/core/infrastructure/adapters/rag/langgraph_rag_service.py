"""
LangGraph implementation of RAG service.
"""
from typing import List, Dict, Any

from core.application.ports.services.rag_service import RAGService
from rag.services import RAGOrchestrator


class LangGraphRAGService(RAGService):
    """LangGraph-based RAG service implementation."""

    def __init__(self):
        """Initialize LangGraph RAG service."""
        self.orchestrator = RAGOrchestrator()

    def process_query(
        self, query: str, chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.

        Args:
            query: User's question
            chat_history: Previous conversation messages

        Returns:
            Dictionary containing answer, citations, metadata, and error
        """
        return self.orchestrator.process_query(query, chat_history or [])
