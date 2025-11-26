"""
Dependency injection configuration for the application.

This module wires together all the hexagonal architecture components:
- Domain entities
- Application use cases
- Infrastructure adapters
"""
from django.conf import settings

# Repositories
from core.infrastructure.adapters.repositories.django_document_repository import (
    DjangoDocumentRepository
)
from core.infrastructure.adapters.repositories.django_chunk_repository import (
    DjangoChunkRepository
)
from core.infrastructure.adapters.repositories.django_chat_repository import (
    DjangoChatSessionRepository,
    DjangoChatMessageRepository
)

# Services
from core.infrastructure.adapters.services.gemini_embedding_service import (
    GeminiEmbeddingService
)
from core.infrastructure.adapters.services.gemini_llm_service import GeminiLLMService
from core.infrastructure.adapters.services.pdf_text_extractor import PDFTextExtractor
from core.infrastructure.adapters.services.docx_text_extractor import DOCXTextExtractor
from core.infrastructure.adapters.services.txt_text_extractor import TXTTextExtractor
from core.infrastructure.adapters.rag.langgraph_rag_service import LangGraphRAGService

# Use cases
from core.application.use_cases.upload_document import UploadDocumentUseCase
from core.application.use_cases.process_document import ProcessDocumentUseCase
from core.application.use_cases.ask_question import AskQuestionUseCase


class DependencyContainer:
    """Container for dependency injection."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize repositories
        self.document_repository = DjangoDocumentRepository()
        self.chunk_repository = DjangoChunkRepository()
        self.chat_session_repository = DjangoChatSessionRepository()
        self.chat_message_repository = DjangoChatMessageRepository()

        # Initialize services
        self.embedding_service = GeminiEmbeddingService()
        self.llm_service = GeminiLLMService()
        self.text_extractors = [
            PDFTextExtractor(),
            DOCXTextExtractor(),
            TXTTextExtractor()
        ]
        self.rag_service = LangGraphRAGService()

        # Initialize use cases
        self.upload_document_use_case = UploadDocumentUseCase(
            document_repository=self.document_repository
        )

        self.process_document_use_case = ProcessDocumentUseCase(
            document_repository=self.document_repository,
            chunk_repository=self.chunk_repository,
            text_extractors=self.text_extractors,
            embedding_service=self.embedding_service,
            chunk_size=getattr(settings, 'CHUNK_SIZE', 800),
            chunk_overlap=getattr(settings, 'CHUNK_OVERLAP', 200)
        )

        self.ask_question_use_case = AskQuestionUseCase(
            chat_session_repository=self.chat_session_repository,
            chat_message_repository=self.chat_message_repository,
            rag_service=self.rag_service
        )

        self._initialized = True


# Global container instance
container = DependencyContainer()


# Convenience functions to get use cases
def get_upload_document_use_case() -> UploadDocumentUseCase:
    """Get the upload document use case."""
    return container.upload_document_use_case


def get_process_document_use_case() -> ProcessDocumentUseCase:
    """Get the process document use case."""
    return container.process_document_use_case


def get_ask_question_use_case() -> AskQuestionUseCase:
    """Get the ask question use case."""
    return container.ask_question_use_case
