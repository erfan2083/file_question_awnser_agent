import google.generativeai as genai
from django.conf import settings
from documents.models import DocumentChunk, Document
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import logging
import numpy as np

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)


class RetrievalService:
    """Service for hybrid retrieval (BM25 + vector search)"""

    def __init__(self):
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self.top_k = settings.TOP_K_RETRIEVAL

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using hybrid search
        """
        try:
            # Get all ready documents
            ready_docs = Document.objects.filter(status=Document.Status.READY)
            if not ready_docs.exists():
                logger.warning("No ready documents available for retrieval")
                return []

            # Get all chunks from ready documents
            chunks = DocumentChunk.objects.filter(
                document__in=ready_docs, embedding__isnull=False
            )

            if not chunks.exists():
                logger.warning("No chunks with embeddings available")
                return []

            # Generate query embedding
            query_embedding = self._generate_embedding(query)

            # Vector similarity search
            vector_results = self._vector_search(chunks, query_embedding)

            # BM25 keyword search
            bm25_results = self._bm25_search(chunks, query)

            # Combine and rerank results
            combined_results = self._combine_results(vector_results, bm25_results)

            # Format results
            formatted_results = []
            for chunk in combined_results[: self.top_k]:
                formatted_results.append(
                    {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document.id,
                        "document_title": chunk.document.title,
                        "chunk_index": chunk.index,
                        "page": chunk.page_number,
                        "text": chunk.text,
                        "snippet": chunk.text[:200] + "..."
                        if len(chunk.text) > 200
                        else chunk.text,
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            return []

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for query"""
        try:
            result = genai.embed_content(
                model=self.embedding_model, content=text, task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return [0.0] * 768

    def _vector_search(
        self, chunks: Any, query_embedding: List[float]
    ) -> List[DocumentChunk]:
        """Perform vector similarity search"""
        try:
            # Calculate cosine similarity for each chunk
            chunks_with_scores = []

            for chunk in chunks:
                if chunk.embedding:
                    similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                    chunks_with_scores.append((chunk, similarity))

            # Sort by similarity score
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)

            return [chunk for chunk, score in chunks_with_scores[: self.top_k * 2]]

        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return list(chunks[: self.top_k])

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def _bm25_search(self, chunks: Any, query: str) -> List[DocumentChunk]:
        """Perform BM25 keyword search"""
        try:
            # Tokenize corpus
            corpus = [chunk.text.lower().split() for chunk in chunks]
            bm25 = BM25Okapi(corpus)

            # Tokenize query
            query_tokens = query.lower().split()

            # Get scores
            scores = bm25.get_scores(query_tokens)

            # Get top chunks
            top_indices = np.argsort(scores)[::-1][: self.top_k * 2]

            chunks_list = list(chunks)
            return [chunks_list[i] for i in top_indices if i < len(chunks_list)]

        except Exception as e:
            logger.error(f"Error in BM25 search: {str(e)}")
            return list(chunks[: self.top_k])

    def _combine_results(
        self, vector_results: List[DocumentChunk], bm25_results: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """Combine and rerank results from both methods"""
        # Use a simple approach: merge and deduplicate, prioritizing vector results
        seen_ids = set()
        combined = []

        # Add vector results first
        for chunk in vector_results:
            if chunk.id not in seen_ids:
                combined.append(chunk)
                seen_ids.add(chunk.id)

        # Add BM25 results
        for chunk in bm25_results:
            if chunk.id not in seen_ids:
                combined.append(chunk)
                seen_ids.add(chunk.id)

        return combined
