"""
Use case for asking a question.
"""
from typing import List

from core.domain.entities.chat import ChatMessage, ChatSession, MessageRole, Citation
from core.domain.exceptions import DocumentNotFoundError
from core.application.ports.repositories.chat_repository import (
    ChatSessionRepository,
    ChatMessageRepository
)
from core.application.ports.services.rag_service import RAGService
from core.application.dto.chat_dto import (
    AskQuestionDTO,
    QuestionResponseDTO,
    CitationDTO
)


class AskQuestionUseCase:
    """Use case for asking a question in a chat session."""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository,
        rag_service: RAGService
    ):
        """
        Initialize use case.

        Args:
            chat_session_repository: Repository for chat sessions
            chat_message_repository: Repository for chat messages
            rag_service: RAG service for question answering
        """
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository
        self.rag_service = rag_service

    def execute(self, dto: AskQuestionDTO) -> QuestionResponseDTO:
        """
        Execute the ask question use case.

        Args:
            dto: Question data

        Returns:
            QuestionResponseDTO with answer and citations

        Raises:
            DocumentNotFoundError: If session not found
        """
        # Get session
        session = self.chat_session_repository.get_by_id(dto.session_id)
        if not session:
            raise DocumentNotFoundError(f"Chat session {dto.session_id} not found")

        # Create user message
        user_message = ChatMessage(
            id=None,
            session_id=dto.session_id,
            role=MessageRole.USER,
            content=dto.question
        )
        saved_user_message = self.chat_message_repository.create(user_message)

        # Get conversation history
        recent_messages = self.chat_message_repository.get_recent_messages(
            dto.session_id, limit=10
        )
        chat_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in recent_messages[:-1]  # Exclude the just-created user message
        ]

        # Process query through RAG
        rag_result = self.rag_service.process_query(
            query=dto.question,
            chat_history=chat_history
        )

        # Create citations
        citations = []
        for citation_data in rag_result.get("citations", []):
            citation = Citation(
                document_id=citation_data["document_id"],
                document_title=citation_data["document_title"],
                chunk_index=citation_data["chunk_index"],
                page=citation_data.get("page"),
                snippet=citation_data["snippet"]
            )
            citations.append(citation)

        # Create assistant message
        assistant_message = ChatMessage(
            id=None,
            session_id=dto.session_id,
            role=MessageRole.ASSISTANT,
            content=rag_result.get("answer", ""),
            citations=citations,
            metadata=rag_result.get("metadata", {})
        )
        saved_assistant_message = self.chat_message_repository.create(assistant_message)

        # Convert to DTO
        citation_dtos = [
            CitationDTO(
                document_id=c.document_id,
                document_title=c.document_title,
                chunk_index=c.chunk_index,
                page=c.page,
                snippet=c.snippet
            )
            for c in citations
        ]

        return QuestionResponseDTO(
            answer=saved_assistant_message.content,
            citations=citation_dtos,
            metadata=saved_assistant_message.metadata,
            message_id=saved_assistant_message.id,
            session_id=dto.session_id
        )
