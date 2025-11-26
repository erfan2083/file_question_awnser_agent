"""
Gemini implementation of LLMService.
"""
from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings

from core.domain.exceptions import LLMError
from core.application.ports.services.llm_service import LLMService


class GeminiLLMService(LLMService):
    """Gemini API implementation of LLM service."""

    def __init__(self):
        """Initialize Gemini LLM service."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            transport="rest"
        )

    def generate_response(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate a response from the LLM."""
        try:
            self.llm.temperature = temperature
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise LLMError(f"Failed to generate response: {str(e)}")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        """Generate a chat response."""
        try:
            self.llm.temperature = temperature
            # Format messages for LangChain
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise LLMError(f"Failed to generate chat response: {str(e)}")
