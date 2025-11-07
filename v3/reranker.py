"""Reranking module for refining retrieval results."""

from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from src.config.settings import settings
from src.models.schemas import RetrievalResult


class Reranker:
    """Reranks retrieval results for better relevance and diversity."""

    def __init__(self, llm: ChatGoogleGenerativeAI = None):
        """
        Initialize reranker.

        Args:
            llm: Language model for reranking
        """
        self.llm = llm or ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key,
        )

    def rerank(
        self, query: str, results: List[RetrievalResult], top_k: int = None
    ) -> List[RetrievalResult]:
        """
        Rerank results using LLM-based relevance scoring.

        Args:
            query: Original query
            results: List of retrieval results
            top_k: Number of top results to return after reranking

        Returns:
            Reranked list of results
        """
        if not results:
            return results

        top_k = top_k or settings.rerank_top_k

        # If we have fewer results than top_k, return all
        if len(results) <= top_k:
            return results

        # Use a simple diversity-based reranking for now
        # In production, you might use cross-encoder models or LLM-based scoring
        reranked = self._diversity_rerank(results, top_k)

        logger.info(f"Reranked {len(results)} results to top {len(reranked)}")

        return reranked

    def _diversity_rerank(
        self, results: List[RetrievalResult], top_k: int
    ) -> List[RetrievalResult]:
        """
        Rerank results to maximize diversity while maintaining relevance.

        Args:
            results: List of retrieval results
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        if not results:
            return []

        selected = []
        remaining = results.copy()

        # Always select the top result
        selected.append(remaining.pop(0))

        # Select remaining results based on diversity
        while len(selected) < top_k and remaining:
            best_candidate = None
            best_score = -1

            for candidate in remaining:
                # Calculate diversity score (how different from already selected)
                diversity_score = self._calculate_diversity(candidate, selected)

                # Combine with relevance score
                combined_score = 0.7 * candidate.score + 0.3 * diversity_score

                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break

        return selected

    def _calculate_diversity(
        self, candidate: RetrievalResult, selected: List[RetrievalResult]
    ) -> float:
        """
        Calculate diversity score for a candidate.

        Args:
            candidate: Candidate result
            selected: Already selected results

        Returns:
            Diversity score (0-1)
        """
        if not selected:
            return 1.0

        # Simple diversity: check if from same document
        candidate_doc_id = candidate.chunk.document_id

        # Count how many selected results are from same document
        same_doc_count = sum(
            1 for s in selected if s.chunk.document_id == candidate_doc_id
        )

        # Penalize if many results from same document
        diversity = 1.0 / (1.0 + same_doc_count)

        return diversity


def rerank_results(
    query: str, results: List[RetrievalResult], top_k: int = None
) -> List[RetrievalResult]:
    """
    Convenience function to rerank results.

    Args:
        query: Original query
        results: List of retrieval results
        top_k: Number of top results to return

    Returns:
        Reranked results
    """
    reranker = Reranker()
    return reranker.rerank(query, results, top_k)
