"""
Chat entities - core domain models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    """Chat message role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Citation:
    """Citation information for an answer."""
    document_id: int
    document_title: str
    chunk_index: int
    page: Optional[int]
    snippet: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_index": self.chunk_index,
            "page": self.page,
            "snippet": self.snippet
        }


@dataclass
class ChatMessage:
    """Chat message entity."""
    id: Optional[int]
    session_id: int
    role: MessageRole
    content: str
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def add_citation(self, citation: Citation) -> None:
        """Add a citation to the message."""
        self.citations.append(citation)

    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER

    def is_from_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT

    def __repr__(self):
        return f"ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})"


@dataclass
class ChatSession:
    """Chat session entity."""
    id: Optional[int]
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[ChatMessage] = field(default_factory=list)

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the session."""
        self.messages.append(message)

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]

    def __repr__(self):
        return f"ChatSession(id={self.id}, title='{self.title}', messages={len(self.messages)})"
