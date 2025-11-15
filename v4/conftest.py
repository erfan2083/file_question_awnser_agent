import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, DocumentChunk
from chat.models import ChatSession, ChatMessage
from evaluation.models import TestQuery, EvaluationRun


@pytest.fixture
def sample_document(db):
    """Create a sample document"""
    doc = Document.objects.create(
        title="Test Document",
        file=SimpleUploadedFile("test.txt", b"Sample content"),
        file_type=Document.FileType.TXT,
        status=Document.Status.READY,
    )
    return doc


@pytest.fixture
def sample_chunk(db, sample_document):
    """Create a sample document chunk"""
    chunk = DocumentChunk.objects.create(
        document=sample_document,
        index=0,
        text="This is a sample text chunk for testing.",
        page_number=1,
        embedding=[0.1] * 768,
    )
    return chunk


@pytest.fixture
def chat_session(db):
    """Create a chat session"""
    session = ChatSession.objects.create(title="Test Session")
    return session


@pytest.fixture
def chat_message(db, chat_session):
    """Create a chat message"""
    message = ChatMessage.objects.create(
        session=chat_session,
        role=ChatMessage.Role.USER,
        content="Test message",
    )
    return message


@pytest.fixture
def test_query(db):
    """Create a test query"""
    query = TestQuery.objects.create(
        query="What is the main topic?",
        expected_keywords=["topic", "main"],
        language="en",
        is_active=True,
    )
    return query


@pytest.fixture
def evaluation_run(db, test_query):
    """Create an evaluation run"""
    run = EvaluationRun.objects.create(total_queries=1, average_score=0.8)
    return run
