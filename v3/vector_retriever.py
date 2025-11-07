"""Vector-based semantic retrieval."""

from typing import Dict, List, Optional

from loguru import logger

from src.document_processing.indexer import DocumentIndexer
from src.models.schemas import DocumentChunk


class VectorRetriever:
    """Vector-based semantic retriever."""

    def __init__(self, indexer: DocumentIndexer = None):
        """
        Initialize vector retriever.

        Args:
            indexer: Document indexer instance
        """
        self.indexer = indexer or DocumentIndexer()

    def retrieve(
        self, query: str, top_k: int = 5, document_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks using vector similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional document ID to filter by

        Returns:
            List of results with chunks and scores
        """
        # Query the vector store
        results = self.indexer.query(
            query_text=query, top_k=top_k, document_id=document_id
        )

        # Format results
        formatted_results = []
        for result in results:
            # Reconstruct DocumentChunk
            chunk = DocumentChunk(
                chunk_id=result["chunk_id"],
                document_id=result["metadata"]["document_id"],
                text=result["text"],
                chunk_index=result["metadata"]["chunk_index"],
                metadata=result["metadata"],
            )

            # Convert distance to similarity score (cosine similarity)
            # ChromaDB returns L2 distance, we convert to similarity
            similarity_score = 1.0 / (1.0 + result["distance"])

            formatted_results.append(
                {"chunk": chunk, "score": similarity_score, "source": "vector"}
            )

        logger.info(
            f"Vector retrieval returned {len(formatted_results)} results for query: {query}"
        )

        return formatted_results

    def get_indexer(self) -> DocumentIndexer:
        """
        Get the document indexer.

        Returns:
            DocumentIndexer instance
        """
        return self.indexer
