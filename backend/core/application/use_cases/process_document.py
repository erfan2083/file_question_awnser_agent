"""
Use case for processing a document (text extraction, chunking, embedding).
"""
from typing import List

from core.domain.entities.document import Document
from core.domain.entities.chunk import DocumentChunk
from core.domain.value_objects.embedding import Embedding
from core.domain.exceptions import (
    DocumentNotFoundError,
    TextExtractionError,
    EmbeddingGenerationError
)
from core.application.ports.repositories.document_repository import DocumentRepository
from core.application.ports.repositories.chunk_repository import ChunkRepository
from core.application.ports.services.text_extractor import TextExtractor
from core.application.ports.services.embedding_service import EmbeddingService
from core.application.dto.document_dto import DocumentProcessingResultDTO


class ProcessDocumentUseCase:
    """Use case for processing a document."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        text_extractors: List[TextExtractor],
        embedding_service: EmbeddingService,
        chunk_size: int = 800,
        chunk_overlap: int = 200
    ):
        """
        Initialize use case.

        Args:
            document_repository: Repository for document persistence
            chunk_repository: Repository for chunk persistence
            text_extractors: List of text extractor services
            embedding_service: Service for generating embeddings
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.text_extractors = text_extractors
        self.embedding_service = embedding_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def execute(self, document_id: int) -> DocumentProcessingResultDTO:
        """
        Execute the document processing use case.

        Args:
            document_id: ID of document to process

        Returns:
            DocumentProcessingResultDTO with processing result
        """
        # Get document
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")

        try:
            # Mark as processing
            document.start_processing()
            self.document_repository.update(document)

            # Extract text
            text, num_pages = self._extract_text(document)

            if not text or not text.strip():
                document.mark_as_failed("No text extracted from document")
                self.document_repository.update(document)
                return DocumentProcessingResultDTO(
                    document_id=document_id,
                    success=False,
                    error_message="No text extracted from document"
                )

            # Chunk text
            text_chunks = self._chunk_text(text)

            # Generate embeddings and create chunk entities
            chunks = []
            for idx, chunk_text in enumerate(text_chunks):
                embedding = self.embedding_service.generate_embedding(
                    chunk_text, task_type="retrieval_document"
                )
                chunk = DocumentChunk(
                    id=None,
                    document_id=document_id,
                    index=idx,
                    text=chunk_text,
                    embedding=embedding,
                    page_number=None  # Can be enhanced later
                )
                chunks.append(chunk)

            # Save chunks
            self.chunk_repository.delete_by_document(document_id)
            self.chunk_repository.save_bulk(chunks)

            # Mark document as ready
            document.mark_as_ready(num_chunks=len(chunks), num_pages=num_pages)
            self.document_repository.update(document)

            return DocumentProcessingResultDTO(
                document_id=document_id,
                success=True,
                num_chunks=len(chunks),
                num_pages=num_pages
            )

        except (TextExtractionError, EmbeddingGenerationError) as e:
            document.mark_as_failed(str(e))
            self.document_repository.update(document)
            return DocumentProcessingResultDTO(
                document_id=document_id,
                success=False,
                error_message=str(e)
            )

    def _extract_text(self, document: Document) -> tuple:
        """Extract text from document using appropriate extractor."""
        for extractor in self.text_extractors:
            if extractor.can_extract(document.file_type):
                return extractor.extract(document.file_path)
        raise TextExtractionError(f"No extractor found for file type: {document.file_type}")

    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces."""
        # Simple chunking - can be replaced with LangChain text splitter
        chunks = []
        text_length = len(text)
        start = 0

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap

        return chunks if chunks else [text]
