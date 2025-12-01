"""
Shared pytest fixtures for all tests.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock, patch, MagicMock
import numpy as np


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture
def sample_document(db):
    """Create a sample document for testing."""
    from documents.models import Document
    return Document.objects.create(
        title="Test Document",
        file_type="pdf",
        file_size=1024,
        status=Document.Status.READY,
        num_chunks=5,
        num_pages=3
    )


@pytest.fixture
def sample_document_uploaded(db):
    """Create a sample document with UPLOADED status."""
    from documents.models import Document
    return Document.objects.create(
        title="Uploaded Document",
        file_type="txt",
        file_size=512,
        status=Document.Status.UPLOADED
    )


@pytest.fixture
def sample_document_processing(db):
    """Create a sample document with PROCESSING status."""
    from documents.models import Document
    return Document.objects.create(
        title="Processing Document",
        file_type="docx",
        file_size=2048,
        status=Document.Status.PROCESSING
    )


@pytest.fixture
def sample_document_failed(db):
    """Create a sample document with FAILED status."""
    from documents.models import Document
    return Document.objects.create(
        title="Failed Document",
        file_type="pdf",
        file_size=4096,
        status=Document.Status.FAILED,
        error_message="Test error message"
    )


@pytest.fixture
def sample_chunk(sample_document):
    """Create a sample document chunk."""
    from documents.models import DocumentChunk
    return DocumentChunk.objects.create(
        document=sample_document,
        index=0,
        text="This is a sample chunk of text for testing purposes.",
        embedding=[0.1] * 768,
        char_count=52,
        token_count=10,
        page_number=1
    )


@pytest.fixture
def multiple_chunks(sample_document):
    """Create multiple chunks for a document."""
    from documents.models import DocumentChunk
    chunks = []
    for i in range(5):
        chunk = DocumentChunk.objects.create(
            document=sample_document,
            index=i,
            text=f"This is chunk number {i} with some test content.",
            embedding=[0.1 + i * 0.01] * 768,
            char_count=50,
            token_count=10,
            page_number=i + 1
        )
        chunks.append(chunk)
    return chunks


@pytest.fixture
def sample_chat_session(db):
    """Create a sample chat session."""
    from chat.models import ChatSession
    return ChatSession.objects.create(
        title="Test Chat Session"
    )


@pytest.fixture
def sample_chat_message(sample_chat_session):
    """Create a sample chat message."""
    from chat.models import ChatMessage
    return ChatMessage.objects.create(
        session=sample_chat_session,
        role=ChatMessage.Role.USER,
        content="What is the main topic of this document?"
    )


@pytest.fixture
def sample_assistant_message(sample_chat_session):
    """Create a sample assistant message with citations."""
    from chat.models import ChatMessage
    return ChatMessage.objects.create(
        session=sample_chat_session,
        role=ChatMessage.Role.ASSISTANT,
        content="The main topic is about AI systems.",
        metadata={
            "citations": [
                {
                    "document_id": 1,
                    "document_title": "Test Doc",
                    "chunk_index": 0,
                    "page": 1,
                    "snippet": "AI systems are..."
                }
            ]
        }
    )


@pytest.fixture
def sample_test_query(db):
    """Create a sample test query for evaluation."""
    from evaluation.models import TestQuery
    return TestQuery.objects.create(
        query="What is machine learning?",
        expected_answer="Machine learning is a subset of AI",
        expected_keywords=["machine", "learning", "AI", "artificial"],
        category="factual",
        language="en",
        is_active=True
    )


@pytest.fixture
def sample_evaluation_run(db):
    """Create a sample evaluation run."""
    from evaluation.models import EvaluationRun
    return EvaluationRun.objects.create(
        run_name="Test Evaluation Run",
        total_queries=10,
        successful_queries=8,
        failed_queries=2,
        average_score=0.75
    )


# ============================================================
# File Fixtures
# ============================================================

@pytest.fixture
def sample_pdf_file():
    """Create a simple PDF file for upload testing."""
    # Minimal PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test PDF Content) Tj ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
%%EOF"""
    return SimpleUploadedFile(
        name="test_document.pdf",
        content=pdf_content,
        content_type="application/pdf"
    )


@pytest.fixture
def sample_txt_file():
    """Create a simple text file for upload testing."""
    content = b"This is a test document.\nIt contains multiple lines.\nUsed for testing purposes."
    return SimpleUploadedFile(
        name="test_document.txt",
        content=content,
        content_type="text/plain"
    )


@pytest.fixture
def sample_docx_file():
    """Create a mock DOCX file for upload testing."""
    # Minimal DOCX is complex, so we use a simple binary
    content = b"PK\x03\x04" + b"\x00" * 100  # Minimal zip header
    return SimpleUploadedFile(
        name="test_document.docx",
        content=content,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@pytest.fixture
def sample_image_file():
    """Create a simple PNG image for upload testing."""
    # 1x1 white PNG
    png_content = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02'
        b'\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return SimpleUploadedFile(
        name="test_image.png",
        content=png_content,
        content_type="image/png"
    )


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_gemini_embedding():
    """Mock Gemini embedding generation."""
    with patch('google.generativeai.embed_content') as mock:
        mock.return_value = {'embedding': [0.1] * 768}
        yield mock


@pytest.fixture
def mock_gemini_llm():
    """Mock Gemini LLM response."""
    with patch('langchain_google_genai.ChatGoogleGenerativeAI') as mock:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="This is a test response.")
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_rag_orchestrator():
    """Mock RAG orchestrator."""
    with patch('rag.services.RAGOrchestrator') as mock:
        mock_instance = MagicMock()
        mock_instance.process_query.return_value = {
            'answer': 'Test answer',
            'citations': [
                {
                    'document_id': 1,
                    'document_title': 'Test Doc',
                    'chunk_index': 0,
                    'page': 1,
                    'snippet': 'Test snippet...'
                }
            ],
            'metadata': {'intent': 'RAG_QUERY'},
            'error': ''
        }
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_document_processor():
    """Mock document processor."""
    with patch('documents.services.DocumentProcessor') as mock:
        mock_instance = MagicMock()
        mock_instance.process_document.return_value = True
        mock.return_value = mock_instance
        yield mock


# ============================================================
# Domain Entity Fixtures
# ============================================================

@pytest.fixture
def document_entity():
    """Create a domain document entity."""
    from core.domain.entities.document import Document
    from core.domain.value_objects.document_status import DocumentStatus
    from core.domain.value_objects.file_type import FileType
    
    return Document(
        id=1,
        title="Test Document Entity",
        file_path="/path/to/file.pdf",
        file_type=FileType.PDF,
        file_size=1024,
        status=DocumentStatus.READY,
        num_chunks=5,
        num_pages=3
    )


@pytest.fixture
def chunk_entity():
    """Create a domain chunk entity."""
    from core.domain.entities.chunk import DocumentChunk
    from core.domain.value_objects.embedding import Embedding
    
    return DocumentChunk(
        id=1,
        document_id=1,
        index=0,
        text="Test chunk content for domain testing.",
        embedding=Embedding([0.1] * 768),
        page_number=1
    )


@pytest.fixture
def chat_session_entity():
    """Create a domain chat session entity."""
    from core.domain.entities.chat import ChatSession
    
    return ChatSession(
        id=1,
        title="Test Session Entity"
    )


@pytest.fixture
def chat_message_entity():
    """Create a domain chat message entity."""
    from core.domain.entities.chat import ChatMessage, MessageRole
    
    return ChatMessage(
        id=1,
        session_id=1,
        role=MessageRole.USER,
        content="Test message content"
    )


# ============================================================
# API Client Fixtures
# ============================================================

@pytest.fixture
def api_client():
    """Create a Django REST framework API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Create an authenticated API client (for future auth implementation)."""
    # Currently no auth, but ready for future
    return api_client
