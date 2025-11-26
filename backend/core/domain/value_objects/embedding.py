"""
Value object for embeddings.
"""
from typing import List
import numpy as np


class Embedding:
    """Vector embedding value object."""

    def __init__(self, vector: List[float], dimensions: int = 768):
        """
        Initialize embedding.

        Args:
            vector: The embedding vector
            dimensions: Expected dimensions
        """
        if len(vector) != dimensions:
            raise ValueError(
                f"Embedding dimension mismatch: expected {dimensions}, got {len(vector)}"
            )
        self._vector = np.array(vector, dtype=np.float32)

    @property
    def vector(self) -> List[float]:
        """Get the embedding vector as a list."""
        return self._vector.tolist()

    @property
    def numpy_array(self) -> np.ndarray:
        """Get the embedding as numpy array."""
        return self._vector

    def cosine_similarity(self, other: 'Embedding') -> float:
        """Calculate cosine similarity with another embedding."""
        dot_product = np.dot(self._vector, other._vector)
        norm_a = np.linalg.norm(self._vector)
        norm_b = np.linalg.norm(other._vector)
        return float(dot_product / (norm_a * norm_b))

    def __eq__(self, other):
        if not isinstance(other, Embedding):
            return False
        return np.array_equal(self._vector, other._vector)

    def __repr__(self):
        return f"Embedding(dimensions={len(self._vector)})"
