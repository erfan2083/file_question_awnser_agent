"""
Django ORM implementation of Chat repositories.
"""
from typing import Optional, List

from chat.models import ChatSession as SessionModel, ChatMessage as MessageModel
from core.domain.entities.chat import (
    ChatSession as SessionEntity,
    ChatMessage as MessageEntity,
    MessageRole,
    Citation
)
from core.application.ports.repositories.chat_repository import (
    ChatSessionRepository,
    ChatMessageRepository
)


class DjangoChatSessionRepository(ChatSessionRepository):
    """Django ORM implementation of chat session repository."""

    def create(self, session: SessionEntity) -> SessionEntity:
        """Create a new chat session."""
        model = SessionModel(
            title=session.title
        )
        model.save()
        return self._to_entity(model)

    def get_by_id(self, session_id: int) -> Optional[SessionEntity]:
        """Get chat session by ID."""
        try:
            model = SessionModel.objects.get(id=session_id)
            return self._to_entity(model)
        except SessionModel.DoesNotExist:
            return None

    def list_all(self) -> List[SessionEntity]:
        """List all chat sessions."""
        models = SessionModel.objects.all()
        return [self._to_entity(model) for model in models]

    def update(self, session: SessionEntity) -> SessionEntity:
        """Update a chat session."""
        try:
            model = SessionModel.objects.get(id=session.id)
            model.title = session.title
            model.save()
            return self._to_entity(model)
        except SessionModel.DoesNotExist:
            return None

    def delete(self, session_id: int) -> bool:
        """Delete a chat session."""
        try:
            model = SessionModel.objects.get(id=session_id)
            model.delete()
            return True
        except SessionModel.DoesNotExist:
            return False

    def _to_entity(self, model: SessionModel) -> SessionEntity:
        """Convert Django model to domain entity."""
        return SessionEntity(
            id=model.id,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class DjangoChatMessageRepository(ChatMessageRepository):
    """Django ORM implementation of chat message repository."""

    def create(self, message: MessageEntity) -> MessageEntity:
        """Create a new chat message."""
        # Convert citations to dict
        citations_data = [
            {
                "document_id": c.document_id,
                "document_title": c.document_title,
                "chunk_index": c.chunk_index,
                "page": c.page,
                "snippet": c.snippet
            }
            for c in message.citations
        ]

        model = MessageModel(
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            metadata={
                **message.metadata,
                "citations": citations_data
            }
        )
        model.save()
        return self._to_entity(model)

    def get_by_session(self, session_id: int) -> List[MessageEntity]:
        """Get all messages for a session."""
        models = MessageModel.objects.filter(session_id=session_id).order_by('created_at')
        return [self._to_entity(model) for model in models]

    def get_recent_messages(self, session_id: int, limit: int = 10) -> List[MessageEntity]:
        """Get recent messages for a session."""
        models = MessageModel.objects.filter(
            session_id=session_id
        ).order_by('-created_at')[:limit]
        # Reverse to get chronological order
        return [self._to_entity(model) for model in reversed(models)]

    def _to_entity(self, model: MessageModel) -> MessageEntity:
        """Convert Django model to domain entity."""
        # Extract citations from metadata
        citations_data = model.metadata.get("citations", [])
        citations = [
            Citation(
                document_id=c["document_id"],
                document_title=c["document_title"],
                chunk_index=c["chunk_index"],
                page=c.get("page"),
                snippet=c["snippet"]
            )
            for c in citations_data
        ]

        # Remove citations from metadata as they're separate in entity
        metadata = {k: v for k, v in model.metadata.items() if k != "citations"}

        return MessageEntity(
            id=model.id,
            session_id=model.session_id,
            role=MessageRole(model.role),
            content=model.content,
            citations=citations,
            metadata=metadata,
            created_at=model.created_at
        )
