"""
LLM service port (interface).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMService(ABC):
    """Service interface for LLM operations."""

    @abstractmethod
    def generate_response(self, prompt: str, temperature: float = 0.3) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        """
        Generate a chat response.

        Args:
            messages: List of chat messages with role and content
            temperature: Sampling temperature

        Returns:
            Generated response

        Raises:
            LLMError: If generation fails
        """
        pass
