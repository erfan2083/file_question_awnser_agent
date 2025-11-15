import pytest
from chat.models import ChatSession, ChatMessage
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestChatSession:
    """Tests for ChatSession model"""

    def test_create_session(self):
        session = ChatSession.objects.create(title="Test Session")
        assert session.title == "Test Session"
        assert str(session) == "Session 1 - Test Session"

    def test_session_without_title(self):
        session = ChatSession.objects.create()
        assert session.title is None


@pytest.mark.django_db
class TestChatMessage:
    """Tests for ChatMessage model"""

    def test_create_message(self, chat_session):
        message = ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.Role.USER,
            content="Hello",
            metadata={"test": "data"},
        )
        assert message.content == "Hello"
        assert message.role == ChatMessage.Role.USER
        assert message.get_citations() == []

    def test_message_with_citations(self, chat_session):
        citations = [{"document_id": 1, "page": 1}]
        message = ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.Role.ASSISTANT,
            content="Answer",
            metadata={"citations": citations},
        )
        assert message.get_citations() == citations


@pytest.mark.django_db
class TestChatAPI:
    """Tests for Chat API endpoints"""

    def test_create_session(self):
        client = APIClient()
        response = client.post("/api/chat/sessions/", {})
        assert response.status_code == 201
        assert "id" in response.data

    def test_list_sessions(self, chat_session):
        client = APIClient()
        response = client.get("/api/chat/sessions/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_get_session_messages(self, chat_session, chat_message):
        client = APIClient()
        response = client.get(f"/api/chat/sessions/{chat_session.id}/messages/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_send_message(self, chat_session, sample_document, sample_chunk):
        client = APIClient()
        response = client.post(
            f"/api/chat/sessions/{chat_session.id}/messages/",
            {"content": "What is this about?"},
            format="json",
        )
        assert response.status_code == 200
        assert "answer" in response.data
        assert "citations" in response.data
