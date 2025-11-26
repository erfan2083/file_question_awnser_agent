"""
Document chunk entity - core domain model.
"""
from typing import Optional
from dataclasses import dataclass

from core.domain.value_objects.embedding import Embedding


@dataclass
class DocumentChunk:
    """
    Document chunk entity representing a text chunk with embedding.

    This is a pure domain entity.
    """

    id: Optional[int]
    document_id: int
    index: int
    text: str
    embedding: Embedding
    page_number: Optional[int] = None
    char_count: int = 0
    token_count: int = 0

    def __post_init__(self):
        """Calculate char and token counts if not provided."""
        if self.char_count == 0:
            self.char_count = len(self.text)
        if self.token_count == 0:
            # Rough approximation
            self.token_count = len(self.text.split())

    def get_snippet(self, max_length: int = 200) -> str:
        """Get a snippet of the chunk text."""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."

    def __repr__(self):
        return f"DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.index})"
