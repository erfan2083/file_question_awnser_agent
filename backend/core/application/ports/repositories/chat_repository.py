"""
Chat repository port (interface).
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from core.domain.entities.chat import ChatSession, ChatMessage


class ChatSessionRepository(ABC):
    """Repository interface for chat session persistence."""

    @abstractmethod
    def create(self, session: ChatSession) -> ChatSession:
        """
        Create a new chat session.

        Args:
            session: Chat session to create

        Returns:
            Created session with ID
        """
        pass

    @abstractmethod
    def get_by_id(self, session_id: int) -> Optional[ChatSession]:
        """
        Get chat session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Chat session if found, None otherwise
        """
        pass

    @abstractmethod
    def list_all(self) -> List[ChatSession]:
        """
        List all chat sessions.

        Returns:
            List of all sessions
        """
        pass

    @abstractmethod
    def update(self, session: ChatSession) -> ChatSession:
        """
        Update a chat session.

        Args:
            session: Session with updated fields

        Returns:
            Updated session
        """
        pass

    @abstractmethod
    def delete(self, session_id: int) -> bool:
        """
        Delete a chat session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False otherwise
        """
        pass


class ChatMessageRepository(ABC):
    """Repository interface for chat message persistence."""

    @abstractmethod
    def create(self, message: ChatMessage) -> ChatMessage:
        """
        Create a new chat message.

        Args:
            message: Chat message to create

        Returns:
            Created message with ID
        """
        pass

    @abstractmethod
    def get_by_session(self, session_id: int) -> List[ChatMessage]:
        """
        Get all messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    def get_recent_messages(self, session_id: int, limit: int = 10) -> List[ChatMessage]:
        """
        Get recent messages for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        pass
