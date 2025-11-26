"""
Gemini implementation of EmbeddingService.
"""
from typing import List

import google.generativeai as genai
from django.conf import settings

from core.domain.value_objects.embedding import Embedding
from core.domain.exceptions import EmbeddingGenerationError
from core.application.ports.services.embedding_service import EmbeddingService


class GeminiEmbeddingService(EmbeddingService):
    """Gemini API implementation of embedding service."""

    def __init__(self):
        """Initialize Gemini embedding service."""
        genai.configure(
            api_key=settings.GOOGLE_API_KEY,
            transport='rest'
        )
        self.model = settings.GEMINI_EMBEDDING_MODEL

    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> Embedding:
        """Generate embedding for text."""
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type=task_type
            )
            return Embedding(result['embedding'])
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}")

    def generate_embeddings_batch(
        self, texts: List[str], task_type: str = "retrieval_document"
    ) -> List[Embedding]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embeddings.append(self.generate_embedding(text, task_type))
        return embeddings
