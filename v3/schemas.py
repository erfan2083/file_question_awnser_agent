"""Data models and schemas for the Document QA System."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentFormat(str, Enum):
    """Supported document formats."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"


class LanguageCode(str, Enum):
    """Supported language codes."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ARABIC = "ar"


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    format: DocumentFormat = Field(..., description="Document format")
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    file_size: int = Field(..., description="File size in bytes")
    num_chunks: int = Field(default=0, description="Number of chunks")
    language: str = Field(default="en", description="Document language")


class DocumentChunk(BaseModel):
    """A chunk of document text with metadata."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    text: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Index of chunk in document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RetrievalResult(BaseModel):
    """Result from document retrieval."""

    chunk: DocumentChunk
    score: float = Field(..., description="Relevance score")
    source: str = Field(..., description="Retrieval source (bm25/vector/hybrid)")


class Question(BaseModel):
    """User question."""

    text: str = Field(..., description="Question text")
    language: str = Field(default="en", description="Question language")
    document_id: Optional[str] = Field(None, description="Specific document to query")


class Answer(BaseModel):
    """Answer to a question."""

    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(default_factory=list, description="Source chunks")
    confidence: float = Field(default=0.0, description="Confidence score")
    language: str = Field(default="en", description="Answer language")
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentType(str, Enum):
    """Types of agents in the system."""

    RETRIEVER = "retriever"
    REASONING = "reasoning"
    UTILITY = "utility"


class AgentState(BaseModel):
    """State of an agent during execution."""

    agent_type: AgentType
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class UtilityTask(str, Enum):
    """Types of utility tasks."""

    TRANSLATE = "translate"
    SUMMARIZE = "summarize"
    CHECKLIST = "checklist"
    EXTRACT_KEYWORDS = "extract_keywords"


class UtilityRequest(BaseModel):
    """Request for utility agent."""

    task: UtilityTask
    text: str = Field(..., description="Input text")
    target_language: Optional[str] = Field(None, description="Target language for translation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class UtilityResponse(BaseModel):
    """Response from utility agent."""

    task: UtilityTask
    result: str = Field(..., description="Task result")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Conversation history."""

    messages: List[Dict[str, str]] = Field(default_factory=list)
    document_id: Optional[str] = None

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.messages.append({"role": role, "content": content})

    def get_context(self, max_messages: int = 10) -> str:
        """Get conversation context as a formatted string."""
        recent_messages = self.messages[-max_messages:]
        return "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages]
        )
