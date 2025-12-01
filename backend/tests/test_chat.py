"""
Comprehensive tests for chat app.
Covers models, views, serializers, and integration.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from chat.models import ChatSession, ChatMessage
from chat.serializers import (
    ChatSessionSerializer,
    ChatSessionListSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
    MessageResponseSerializer
)


# ============================================================
# Model Tests
# ============================================================

@pytest.mark.django_db
class TestChatSessionModel:
    """Tests for ChatSession model."""
    
    def test_create_session(self):
        """Test creating a chat session."""
        session = ChatSession.objects.create(title="Test Session")
        
        assert session.id is not None
        assert session.title == "Test Session"
        assert session.created_at is not None
        assert session.updated_at is not None
    
    def test_session_str_representation(self):
        """Test session string representation."""
        session = ChatSession.objects.create(title="My Chat")
        
        assert str(session) == f"Session {session.id} - My Chat"
    
    def test_session_without_title(self):
        """Test session without title."""
        session = ChatSession.objects.create()
        
        assert str(session) == f"Session {session.id} - Untitled"
    
    def test_session_ordering(self):
        """Test sessions are ordered by created_at descending."""
        session1 = ChatSession.objects.create(title="Session 1")
        session2 = ChatSession.objects.create(title="Session 2")
        session3 = ChatSession.objects.create(title="Session 3")
        
        sessions = list(ChatSession.objects.all())
        assert sessions[0] == session3
        assert sessions[1] == session2
        assert sessions[2] == session1


@pytest.mark.django_db
class TestChatMessageModel:
    """Tests for ChatMessage model."""
    
    def test_create_user_message(self, sample_chat_session):
        """Test creating a user message."""
        message = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.USER,
            content="Hello, what is AI?"
        )
        
        assert message.id is not None
        assert message.session == sample_chat_session
        assert message.role == ChatMessage.Role.USER
        assert message.content == "Hello, what is AI?"
    
    def test_create_assistant_message(self, sample_chat_session):
        """Test creating an assistant message."""
        message = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.ASSISTANT,
            content="AI stands for Artificial Intelligence.",
            metadata={"citations": []}
        )
        
        assert message.role == ChatMessage.Role.ASSISTANT
        assert message.metadata == {"citations": []}
    
    def test_message_str_representation(self, sample_chat_session):
        """Test message string representation."""
        message = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.USER,
            content="This is a very long message that should be truncated in the string representation"
        )
        
        assert "user:" in str(message).lower()
        assert "..." in str(message)
    
    def test_message_roles(self, sample_chat_session):
        """Test all message role choices."""
        roles = [
            ChatMessage.Role.USER,
            ChatMessage.Role.ASSISTANT,
            ChatMessage.Role.SYSTEM
        ]
        
        for role in roles:
            message = ChatMessage.objects.create(
                session=sample_chat_session,
                role=role,
                content=f"Message with role {role}"
            )
            assert message.role == role
    
    def test_message_ordering(self, sample_chat_session):
        """Test messages are ordered by session and created_at."""
        msg1 = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.USER,
            content="First"
        )
        msg2 = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.ASSISTANT,
            content="Second"
        )
        msg3 = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.USER,
            content="Third"
        )
        
        messages = list(sample_chat_session.messages.all())
        assert messages[0] == msg1
        assert messages[1] == msg2
        assert messages[2] == msg3
    
    def test_message_cascade_delete(self, sample_chat_session):
        """Test that messages are deleted when session is deleted."""
        for i in range(3):
            ChatMessage.objects.create(
                session=sample_chat_session,
                role=ChatMessage.Role.USER,
                content=f"Message {i}"
            )
        
        session_id = sample_chat_session.id
        sample_chat_session.delete()
        
        assert ChatMessage.objects.filter(session_id=session_id).count() == 0
    
    def test_message_with_metadata(self, sample_chat_session):
        """Test message with complex metadata."""
        metadata = {
            "citations": [
                {"document_id": 1, "page": 1},
                {"document_id": 2, "page": 5}
            ],
            "intent": "RAG_QUERY",
            "confidence": 0.95
        }
        
        message = ChatMessage.objects.create(
            session=sample_chat_session,
            role=ChatMessage.Role.ASSISTANT,
            content="Answer with citations",
            metadata=metadata
        )
        
        assert message.metadata["citations"][0]["document_id"] == 1
        assert message.metadata["intent"] == "RAG_QUERY"
        assert message.metadata["confidence"] == 0.95


# ============================================================
# Serializer Tests
# ============================================================

@pytest.mark.django_db
class TestChatSerializers:
    """Tests for chat serializers."""
    
    def test_chat_session_serializer(self, sample_chat_session):
        """Test ChatSessionSerializer."""
        serializer = ChatSessionSerializer(sample_chat_session)
        data = serializer.data
        
        assert data['id'] == sample_chat_session.id
        assert data['title'] == sample_chat_session.title
        assert 'messages' in data
        assert 'message_count' in data
    
    def test_chat_session_list_serializer(self, sample_chat_session, sample_chat_message):
        """Test ChatSessionListSerializer."""
        serializer = ChatSessionListSerializer(sample_chat_session)
        data = serializer.data
        
        assert data['id'] == sample_chat_session.id
        assert 'message_count' in data
        assert 'last_message' in data
    
    def test_chat_message_serializer(self, sample_chat_message):
        """Test ChatMessageSerializer."""
        serializer = ChatMessageSerializer(sample_chat_message)
        data = serializer.data
        
        assert data['id'] == sample_chat_message.id
        assert data['role'] == sample_chat_message.role
        assert data['content'] == sample_chat_message.content
    
    def test_send_message_serializer_valid(self):
        """Test SendMessageSerializer with valid data."""
        data = {'content': 'What is machine learning?'}
        serializer = SendMessageSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['content'] == 'What is machine learning?'
    
    def test_send_message_serializer_empty(self):
        """Test SendMessageSerializer with empty content."""
        data = {'content': ''}
        serializer = SendMessageSerializer(data=data)
        
        # Empty string should still be valid (view handles this)
        assert serializer.is_valid()
    
    def test_message_response_serializer(self):
        """Test MessageResponseSerializer."""
        data = {
            'answer': 'This is the answer',
            'citations': [{'doc_id': 1}],
            'session_id': 1,
            'message_id': 1,
            'metadata': {'intent': 'RAG_QUERY'}
        }
        serializer = MessageResponseSerializer(data)
        
        assert serializer.data['answer'] == 'This is the answer'
        assert serializer.data['session_id'] == 1


# ============================================================
# View Tests
# ============================================================

@pytest.mark.django_db
class TestChatSessionViews:
    """Tests for chat session views."""
    
    def test_create_session(self, api_client):
        """Test creating a chat session."""
        response = api_client.post(
            '/api/chat/sessions/',
            {'title': 'New Chat Session'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['title'] == 'New Chat Session'
    
    def test_list_sessions(self, api_client, sample_chat_session):
        """Test listing chat sessions."""
        response = api_client.get('/api/chat/sessions/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_retrieve_session(self, api_client, sample_chat_session):
        """Test retrieving a chat session."""
        response = api_client.get(f'/api/chat/sessions/{sample_chat_session.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['title'] == sample_chat_session.title
    
    def test_delete_session(self, api_client, sample_chat_session):
        """Test deleting a chat session."""
        session_id = sample_chat_session.id
        response = api_client.delete(f'/api/chat/sessions/{session_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChatSession.objects.filter(id=session_id).exists()
    
    def test_get_messages(self, api_client, sample_chat_session, sample_chat_message):
        """Test getting messages for a session."""
        response = api_client.get(
            f'/api/chat/sessions/{sample_chat_session.id}/messages/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
    
    @patch('chat.views.RAGOrchestrator')
    def test_send_message(self, mock_rag, api_client, sample_chat_session):
        """Test sending a message."""
        mock_rag.return_value.process_query.return_value = {
            'answer': 'This is the answer',
            'citations': [],
            'metadata': {'intent': 'RAG_QUERY'},
            'error': ''
        }
        
        response = api_client.post(
            f'/api/chat/sessions/{sample_chat_session.id}/messages/',
            {'content': 'What is AI?'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'answer' in data
        assert data['answer'] == 'This is the answer'
    
    @patch('chat.views.RAGOrchestrator')
    def test_send_message_with_error(self, mock_rag, api_client, sample_chat_session):
        """Test sending a message when RAG returns error."""
        mock_rag.return_value.process_query.return_value = {
            'answer': '',
            'citations': [],
            'metadata': {},
            'error': 'Processing failed'
        }
        
        response = api_client.post(
            f'/api/chat/sessions/{sample_chat_session.id}/messages/',
            {'content': 'What is AI?'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        # Should return an apology message
        data = response.json()
        assert 'error' in data['answer'].lower() or 'apologize' in data['answer'].lower()
    
    def test_clear_messages(self, api_client, sample_chat_session, sample_chat_message):
        """Test clearing messages from a session."""
        response = api_client.delete(
            f'/api/chat/sessions/{sample_chat_session.id}/clear/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert sample_chat_session.messages.count() == 0


@pytest.mark.django_db
class TestChatMessageViews:
    """Tests for chat message views."""
    
    def test_list_messages(self, api_client, sample_chat_message):
        """Test listing messages."""
        response = api_client.get('/api/chat/messages/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_messages_by_session(self, api_client, sample_chat_session, sample_chat_message):
        """Test filtering messages by session."""
        response = api_client.get(
            f'/api/chat/messages/?session_id={sample_chat_session.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# Integration Tests
# ============================================================

@pytest.mark.django_db
class TestChatIntegration:
    """Integration tests for chat functionality."""
    
    @patch('chat.views.RAGOrchestrator')
    def test_full_conversation_flow(self, mock_rag, api_client):
        """Test a complete conversation flow."""
        # Mock RAG responses
        mock_rag.return_value.process_query.side_effect = [
            {
                'answer': 'AI is artificial intelligence.',
                'citations': [{'document_id': 1, 'document_title': 'AI Doc', 'chunk_index': 0, 'page': 1, 'snippet': 'AI...'}],
                'metadata': {'intent': 'RAG_QUERY'},
                'error': ''
            },
            {
                'answer': 'Machine learning is a subset of AI.',
                'citations': [],
                'metadata': {'intent': 'RAG_QUERY'},
                'error': ''
            }
        ]
        
        # Create session
        response = api_client.post(
            '/api/chat/sessions/',
            {'title': 'Test Conversation'},
            format='json'
        )
        session_id = response.json()['id']
        
        # Send first message
        response = api_client.post(
            f'/api/chat/sessions/{session_id}/messages/',
            {'content': 'What is AI?'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Send second message
        response = api_client.post(
            f'/api/chat/sessions/{session_id}/messages/',
            {'content': 'What is machine learning?'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify messages were stored
        response = api_client.get(f'/api/chat/sessions/{session_id}/messages/')
        messages = response.json()
        
        # Should have 4 messages (2 user + 2 assistant)
        assert len(messages) == 4
    
    def test_persian_message(self, api_client, sample_chat_session):
        """Test sending a Persian message."""
        with patch('chat.views.RAGOrchestrator') as mock_rag:
            mock_rag.return_value.process_query.return_value = {
                'answer': 'این یک پاسخ تست است.',
                'citations': [],
                'metadata': {'intent': 'RAG_QUERY'},
                'error': ''
            }
            
            response = api_client.post(
                f'/api/chat/sessions/{sample_chat_session.id}/messages/',
                {'content': 'هوش مصنوعی چیست؟'},
                format='json'
            )
            
            assert response.status_code == status.HTTP_200_OK
