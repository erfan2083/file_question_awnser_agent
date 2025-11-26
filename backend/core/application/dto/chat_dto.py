"""
Data Transfer Objects for chat.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class CitationDTO:
    """DTO for citation."""
    document_id: int
    document_title: str
    chunk_index: int
    page: Optional[int]
    snippet: str


@dataclass
class ChatMessageDTO:
    """DTO for chat message."""
    id: int
    session_id: int
    role: str
    content: str
    citations: List[CitationDTO]
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class ChatSessionDTO:
    """DTO for chat session."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


@dataclass
class AskQuestionDTO:
    """DTO for asking a question."""
    session_id: int
    question: str


@dataclass
class QuestionResponseDTO:
    """DTO for question response."""
    answer: str
    citations: List[CitationDTO]
    metadata: Dict[str, Any]
    message_id: int
    session_id: int
