"""Configuration settings for the Document QA System."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Google Gemini API Configuration
    google_api_key: str = Field(..., description="Google Gemini API key")

    # Vector Store Configuration
    chroma_persist_directory: str = Field(
        default="./data/vectorstore", description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="documents", description="ChromaDB collection name"
    )

    # Document Processing Configuration
    chunk_size: int = Field(default=1000, description="Size of text chunks")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    max_upload_size: int = Field(default=10485760, description="Max upload size in bytes (10MB)")

    # Retrieval Configuration
    top_k_retrieval: int = Field(default=5, description="Number of documents to retrieve")
    rerank_top_k: int = Field(default=3, description="Number of documents after reranking")
    bm25_weight: float = Field(default=0.5, description="Weight for BM25 score")
    vector_weight: float = Field(default=0.5, description="Weight for vector similarity score")

    # Model Configuration
    embedding_model: str = Field(
        default="models/embedding-001", description="Google embedding model"
    )
    llm_model: str = Field(default="gemini-1.5-flash", description="Gemini LLM model")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    max_output_tokens: int = Field(default=2048, description="Maximum output tokens")

    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")

    # Multilingual Support
    supported_languages: str = Field(
        default="en,es,fr,de,ar", description="Comma-separated list of supported languages"
    )
    default_language: str = Field(default="en", description="Default language")

    @property
    def supported_languages_list(self) -> List[str]:
        """Get list of supported languages."""
        return [lang.strip() for lang in self.supported_languages.split(",")]


# Global settings instance
settings = Settings()
