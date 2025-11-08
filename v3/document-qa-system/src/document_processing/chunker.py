"""Document text chunking with overlap."""

from typing import List

from loguru import logger

from src.config.settings import settings
from src.models.schemas import DocumentChunk, DocumentMetadata
from src.utils.helpers import generate_id


class DocumentChunker:
    """Splits documents into overlapping chunks."""

    def __init__(
        self, chunk_size: int = None, chunk_overlap: int = None, separator: str = " "
    ):
        """
        Initialize document chunker.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            separator: Character(s) to use for splitting
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.separator = separator

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    def chunk_text(
        self, text: str, metadata: DocumentMetadata
    ) -> List[DocumentChunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: Input text to chunk
            metadata: Document metadata

        Returns:
            List of DocumentChunk objects
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for document {metadata.document_id}")
            return []

        # Split text into words/tokens
        tokens = text.split(self.separator)

        chunks = []
        chunk_index = 0
        start_idx = 0

        while start_idx < len(tokens):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(tokens))

            # Extract chunk tokens
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.separator.join(chunk_tokens)

            # Create chunk ID
            chunk_id = generate_id(
                f"{metadata.document_id}_{chunk_index}", prefix="chunk_"
            )

            # Create DocumentChunk
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=metadata.document_id,
                text=chunk_text,
                chunk_index=chunk_index,
                metadata={
                    "start_char": start_idx,
                    "end_char": end_idx,
                    "document_filename": metadata.filename,
                },
            )

            chunks.append(chunk)

            # Move to next chunk with overlap
            if end_idx >= len(tokens):
                break

            start_idx = end_idx - self.chunk_overlap
            chunk_index += 1

        logger.info(
            f"Chunked document {metadata.document_id} into {len(chunks)} chunks"
        )

        return chunks

    def chunk_by_sentences(
        self, text: str, metadata: DocumentMetadata, max_sentences: int = 10
    ) -> List[DocumentChunk]:
        """
        Split text into chunks by sentences.

        Args:
            text: Input text to chunk
            metadata: Document metadata
            max_sentences: Maximum number of sentences per chunk

        Returns:
            List of DocumentChunk objects
        """
        import re

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        chunk_index = 0
        current_chunk = []

        for sentence in sentences:
            current_chunk.append(sentence)

            if len(current_chunk) >= max_sentences:
                chunk_text = " ".join(current_chunk)
                chunk_id = generate_id(
                    f"{metadata.document_id}_{chunk_index}", prefix="chunk_"
                )

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.document_id,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    metadata={"document_filename": metadata.filename},
                )

                chunks.append(chunk)
                current_chunk = []
                chunk_index += 1

        # Add remaining sentences as final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_id = generate_id(
                f"{metadata.document_id}_{chunk_index}", prefix="chunk_"
            )

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=metadata.document_id,
                text=chunk_text,
                chunk_index=chunk_index,
                metadata={"document_filename": metadata.filename},
            )

            chunks.append(chunk)

        logger.info(
            f"Chunked document {metadata.document_id} by sentences into {len(chunks)} chunks"
        )

        return chunks


def chunk_document(
    text: str, metadata: DocumentMetadata, method: str = "token"
) -> List[DocumentChunk]:
    """
    Convenience function to chunk a document.

    Args:
        text: Input text to chunk
        metadata: Document metadata
        method: Chunking method ('token' or 'sentence')

    Returns:
        List of DocumentChunk objects
    """
    chunker = DocumentChunker()

    if method == "token":
        return chunker.chunk_text(text, metadata)
    elif method == "sentence":
        return chunker.chunk_by_sentences(text, metadata)
    else:
        raise ValueError(f"Unknown chunking method: {method}")
