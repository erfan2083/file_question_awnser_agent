"""BM25-based keyword retrieval."""

from typing import Dict, List

from loguru import logger
from rank_bm25 import BM25Okapi

from src.models.schemas import DocumentChunk


class BM25Retriever:
    """BM25 keyword-based retriever."""

    def __init__(self):
        """Initialize BM25 retriever."""
        self.corpus: List[DocumentChunk] = []
        self.bm25: BM25Okapi = None
        self.tokenized_corpus: List[List[str]] = []

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Index document chunks for BM25 retrieval.

        Args:
            chunks: List of document chunks to index
        """
        if not chunks:
            logger.warning("No chunks provided for BM25 indexing")
            return

        self.corpus = chunks

        # Tokenize corpus
        self.tokenized_corpus = [self._tokenize(chunk.text) for chunk in chunks]

        # Initialize BM25
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        logger.info(f"Indexed {len(chunks)} chunks for BM25 retrieval")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Simple tokenization (can be improved with better NLP)
        return text.lower().split()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks using BM25.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of results with chunks and scores
        """
        if self.bm25 is None:
            logger.warning("BM25 not initialized. No chunks indexed.")
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        # Format results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include relevant results
                results.append(
                    {
                        "chunk": self.corpus[idx],
                        "score": float(scores[idx]),
                        "source": "bm25",
                    }
                )

        logger.info(f"BM25 retrieval returned {len(results)} results for query: {query}")

        return results

    def get_corpus_size(self) -> int:
        """
        Get the size of the indexed corpus.

        Returns:
            Number of indexed chunks
        """
        return len(self.corpus)

    def clear(self) -> None:
        """Clear the BM25 index."""
        self.corpus = []
        self.bm25 = None
        self.tokenized_corpus = []
        logger.info("Cleared BM25 index")
