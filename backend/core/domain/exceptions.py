"""
Domain exceptions for the application.
"""


class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class DocumentNotFoundError(DomainException):
    """Raised when a document is not found."""
    pass


class DocumentProcessingError(DomainException):
    """Raised when document processing fails."""
    pass


class InvalidDocumentStateError(DomainException):
    """Raised when attempting invalid state transition."""
    pass


class TextExtractionError(DomainException):
    """Raised when text extraction from document fails."""
    pass


class EmbeddingGenerationError(DomainException):
    """Raised when embedding generation fails."""
    pass


class RetrievalError(DomainException):
    """Raised when retrieval operation fails."""
    pass


class LLMError(DomainException):
    """Raised when LLM operation fails."""
    pass
