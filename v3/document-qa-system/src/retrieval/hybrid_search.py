"""Hybrid retrieval combining BM25 and vector search."""

from typing import Dict, List, Optional

from loguru import logger

from src.config.settings import settings
from src.models.schemas import RetrievalResult
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.vector_retriever import VectorRetriever
from src.utils.helpers import calculate_similarity_score


class HybridRetriever:
    """Hybrid retriever combining BM25 and vector search."""

    def __init__(
        self,
        vector_retriever: VectorRetriever = None,
        bm25_retriever: BM25Retriever = None,
        bm25_weight: float = None,
        vector_weight: float = None,
    ):
        """
        Initialize hybrid retriever.

        Args:
            vector_retriever: Vector retriever instance
            bm25_retriever: BM25 retriever instance
            bm25_weight: Weight for BM25 scores
            vector_weight: Weight for vector scores
        """
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.bm25_weight = bm25_weight or settings.bm25_weight
        self.vector_weight = vector_weight or settings.vector_weight

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        document_id: Optional[str] = None,
        use_reranking: bool = True,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks using hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional document ID to filter by
            use_reranking: Whether to apply reranking

        Returns:
            List of RetrievalResult objects
        """
        top_k = top_k or settings.top_k_retrieval

        # Get results from both retrievers
        vector_results = self.vector_retriever.retrieve(
            query=query, top_k=top_k * 2, document_id=document_id
        )
        bm25_results = self.bm25_retriever.retrieve(query=query, top_k=top_k * 2)

        # Normalize scores
        vector_results = self._normalize_scores(vector_results)
        bm25_results = self._normalize_scores(bm25_results)

        # Combine results
        combined_results = self._combine_results(vector_results, bm25_results)

        # Sort by hybrid score
        combined_results.sort(key=lambda x: x["score"], reverse=True)

        # Take top-k
        top_results = combined_results[:top_k]

        # Convert to RetrievalResult objects
        retrieval_results = [
            RetrievalResult(
                chunk=result["chunk"], score=result["score"], source="hybrid"
            )
            for result in top_results
        ]

        logger.info(
            f"Hybrid retrieval returned {len(retrieval_results)} results for query: {query}"
        )

        # Apply reranking if requested
        if use_reranking and len(retrieval_results) > 1:
            from src.retrieval.reranker import rerank_results

            retrieval_results = rerank_results(query, retrieval_results)

        return retrieval_results

    def _normalize_scores(self, results: List[Dict]) -> List[Dict]:
        """
        Normalize scores to [0, 1] range.

        Args:
            results: List of results with scores

        Returns:
            Results with normalized scores
        """
        if not results:
            return results

        scores = [r["score"] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            # All scores are the same
            for result in results:
                result["normalized_score"] = 1.0
        else:
            for result in results:
                result["normalized_score"] = (result["score"] - min_score) / (
                    max_score - min_score
                )

        return results

    def _combine_results(
        self, vector_results: List[Dict], bm25_results: List[Dict]
    ) -> List[Dict]:
        """
        Combine and merge results from both retrievers.

        Args:
            vector_results: Results from vector retriever
            bm25_results: Results from BM25 retriever

        Returns:
            Combined results with hybrid scores
        """
        # Create a mapping of chunk_id to results
        result_map: Dict[str, Dict] = {}

        # Add vector results
        for result in vector_results:
            chunk_id = result["chunk"].chunk_id
            result_map[chunk_id] = {
                "chunk": result["chunk"],
                "vector_score": result.get("normalized_score", 0.0),
                "bm25_score": 0.0,
            }

        # Add/merge BM25 results
        for result in bm25_results:
            chunk_id = result["chunk"].chunk_id
            if chunk_id in result_map:
                result_map[chunk_id]["bm25_score"] = result.get(
                    "normalized_score", 0.0
                )
            else:
                result_map[chunk_id] = {
                    "chunk": result["chunk"],
                    "vector_score": 0.0,
                    "bm25_score": result.get("normalized_score", 0.0),
                }

        # Calculate hybrid scores
        combined_results = []
        for chunk_id, data in result_map.items():
            hybrid_score = calculate_similarity_score(
                bm25_score=data["bm25_score"],
                vector_score=data["vector_score"],
                bm25_weight=self.bm25_weight,
                vector_weight=self.vector_weight,
            )

            combined_results.append({"chunk": data["chunk"], "score": hybrid_score})

        return combined_results

    def get_retrievers(self) -> tuple:
        """
        Get the underlying retrievers.

        Returns:
            Tuple of (vector_retriever, bm25_retriever)
        """
        return self.vector_retriever, self.bm25_retriever
