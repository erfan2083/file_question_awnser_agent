"""
Comprehensive tests for domain layer (hexagonal architecture).
Covers entities, value objects, and domain exceptions.
"""

import pytest
from datetime import datetime
import numpy as np

from core.domain.entities.document import Document
from core.domain.entities.chunk import DocumentChunk
from core.domain.entities.chat import ChatSession, ChatMessage, Citation, MessageRole
from core.domain.value_objects.document_status import DocumentStatus
from core.domain.value_objects.file_type import FileType
from core.domain.value_objects.embedding import Embedding
from core.domain.exceptions import (
    InvalidDocumentStateError,
    DocumentNotFoundError,
    TextExtractionError,
    EmbeddingGenerationError
)


# ============================================================
# Document Entity Tests
# ============================================================

class TestDocumentEntity:
    """Tests for Document domain entity."""
    
    def test_create_document(self):
        """Test creating a document entity."""
        doc = Document(
            id=1,
            title="Test Document",
            file_path="/path/to/file.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            status=DocumentStatus.UPLOADED
        )
        
        assert doc.id == 1
        assert doc.title == "Test Document"
        assert doc.file_type == FileType.PDF
        assert doc.status == DocumentStatus.UPLOADED
    
    def test_start_processing(self):
        """Test transitioning to PROCESSING status."""
        doc = Document(
            id=1,
            title="Test",
            file_path="/path",
            file_type=FileType.PDF,
            file_size=100,
            status=DocumentStatus.UPLOADED
        )
        
        doc.start_processing()
        
        assert doc.status == DocumentStatus.PROCESSING
        assert doc.error_message is None
    
    def test_start_processing_from_failed(self):
        """Test reprocessing a failed document."""
        doc = Document(
            id=1,
            title="Test",
            file_path="/path",
            file_type=FileType.PDF,
            file_size=100,
            status=DocumentStatus.FAILED,
            error_message="Previous error"
        )
        
        doc.start_processing()
        
        assert doc.status == DocumentStatus.PROCESSING
        assert doc.error_message is None
    
    def test_start_processing_invalid_state(self):
        """Test that processing can't start from READY."""
        doc = Document(
            id=1,
            title="Test",
            file_path="/path",
            file_type=FileType.PDF,
            file_size=100,
            status=DocumentStatus.READY
        )
        
        with pytest.raises(InvalidDocumentStateError):
            doc.start_processing()
    
    def test_mark_as_ready(self):
        """Test marking document as ready."""
        doc = Document(
            id=1,
            title="Test",
            file_path="/path",
            file_type=FileType.PDF,
            file_size=100,
            status=DocumentStatus.PROCESSING
        )
        
        doc.mark_as_ready(num_chunks=10, num_pages=5)
        
        assert doc.status == DocumentStatus.READY
        assert doc.num_chunks == 10
        assert doc.num_pages == 5
        assert doc.processed_at is not None
    
    def test_mark_as_failed(self):
        """Test marking document as failed."""
        doc = Document(
            id=1,
            title="Test",
            file_path="/path",
            file_type=FileType.PDF,
            file_size=100,
            status=DocumentStatus.PROCESSING
        )
        
        doc.mark_as_failed("Processing error occurred")
        
        assert doc.status == DocumentStatus.FAILED
        assert doc.error_message == "Processing error occurred"
    
    def test_is_ready(self):
        """Test is_ready method."""
        doc = Document(
            id=1, title="Test", file_path="/path",
            file_type=FileType.PDF, file_size=100,
            status=DocumentStatus.READY
        )
        
        assert doc.is_ready() is True
        
        doc.status = DocumentStatus.PROCESSING
        assert doc.is_ready() is False
    
    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(
            id=1, title="Test Doc", file_path="/path",
            file_type=FileType.PDF, file_size=100,
            status=DocumentStatus.READY
        )
        
        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "Test Doc" in repr_str
        assert "READY" in repr_str


# ============================================================
# DocumentChunk Entity Tests
# ============================================================

class TestDocumentChunkEntity:
    """Tests for DocumentChunk domain entity."""
    
    def test_create_chunk(self):
        """Test creating a chunk entity."""
        embedding = Embedding([0.1] * 768)
        chunk = DocumentChunk(
            id=1,
            document_id=1,
            index=0,
            text="Test chunk content",
            embedding=embedding
        )
        
        assert chunk.id == 1
        assert chunk.document_id == 1
        assert chunk.index == 0
        assert chunk.char_count == len("Test chunk content")
    
    def test_get_snippet(self):
        """Test getting a snippet from chunk."""
        embedding = Embedding([0.1] * 768)
        chunk = DocumentChunk(
            id=1,
            document_id=1,
            index=0,
            text="This is a very long text " * 50,
            embedding=embedding
        )
        
        snippet = chunk.get_snippet(max_length=100)
        
        assert len(snippet) <= 103  # 100 + "..."
        assert snippet.endswith("...")
    
    def test_get_snippet_short_text(self):
        """Test snippet with short text."""
        embedding = Embedding([0.1] * 768)
        chunk = DocumentChunk(
            id=1,
            document_id=1,
            index=0,
            text="Short text",
            embedding=embedding
        )
        
        snippet = chunk.get_snippet(max_length=100)
        
        assert snippet == "Short text"
    
    def test_chunk_repr(self):
        """Test chunk string representation."""
        embedding = Embedding([0.1] * 768)
        chunk = DocumentChunk(
            id=5,
            document_id=2,
            index=3,
            text="Test",
            embedding=embedding
        )
        
        repr_str = repr(chunk)
        assert "DocumentChunk" in repr_str
        assert "5" in repr_str


# ============================================================
# Chat Entity Tests
# ============================================================

class TestChatEntities:
    """Tests for Chat domain entities."""
    
    def test_create_chat_session(self):
        """Test creating a chat session."""
        session = ChatSession(
            id=1,
            title="Test Session"
        )
        
        assert session.id == 1
        assert session.title == "Test Session"
        assert session.messages == []
    
    def test_add_message_to_session(self):
        """Test adding a message to session."""
        session = ChatSession(id=1, title="Test")
        message = ChatMessage(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content="Hello"
        )
        
        session.add_message(message)
        
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        session = ChatSession(id=1, title="Test")
        session.add_message(ChatMessage(
            id=1, session_id=1, role=MessageRole.USER, content="Hi"
        ))
        session.add_message(ChatMessage(
            id=2, session_id=1, role=MessageRole.ASSISTANT, content="Hello!"
        ))
        
        history = session.get_conversation_history()
        
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hi"}
        assert history[1] == {"role": "assistant", "content": "Hello!"}
    
    def test_create_chat_message(self):
        """Test creating a chat message."""
        message = ChatMessage(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content="What is AI?"
        )
        
        assert message.is_from_user() is True
        assert message.is_from_assistant() is False
    
    def test_chat_message_with_citation(self):
        """Test adding citations to message."""
        message = ChatMessage(
            id=1,
            session_id=1,
            role=MessageRole.ASSISTANT,
            content="AI is..."
        )
        
        citation = Citation(
            document_id=1,
            document_title="AI Guide",
            chunk_index=0,
            page=1,
            snippet="AI stands for..."
        )
        
        message.add_citation(citation)
        
        assert len(message.citations) == 1
        assert message.citations[0].document_title == "AI Guide"
    
    def test_citation_to_dict(self):
        """Test citation to dictionary conversion."""
        citation = Citation(
            document_id=1,
            document_title="Test Doc",
            chunk_index=0,
            page=5,
            snippet="Test snippet"
        )
        
        data = citation.to_dict()
        
        assert data["document_id"] == 1
        assert data["document_title"] == "Test Doc"
        assert data["page"] == 5


# ============================================================
# Value Object Tests
# ============================================================

class TestDocumentStatus:
    """Tests for DocumentStatus value object."""
    
    def test_status_values(self):
        """Test all status values."""
        assert DocumentStatus.UPLOADED.value == "UPLOADED"
        assert DocumentStatus.PROCESSING.value == "PROCESSING"
        assert DocumentStatus.READY.value == "READY"
        assert DocumentStatus.FAILED.value == "FAILED"
    
    def test_can_transition_from_uploaded(self):
        """Test valid transitions from UPLOADED."""
        assert DocumentStatus.UPLOADED.can_transition_to(DocumentStatus.PROCESSING) is True
        assert DocumentStatus.UPLOADED.can_transition_to(DocumentStatus.FAILED) is True
        assert DocumentStatus.UPLOADED.can_transition_to(DocumentStatus.READY) is False
    
    def test_can_transition_from_processing(self):
        """Test valid transitions from PROCESSING."""
        assert DocumentStatus.PROCESSING.can_transition_to(DocumentStatus.READY) is True
        assert DocumentStatus.PROCESSING.can_transition_to(DocumentStatus.FAILED) is True
        assert DocumentStatus.PROCESSING.can_transition_to(DocumentStatus.UPLOADED) is False
    
    def test_can_transition_from_ready(self):
        """Test that READY is terminal."""
        assert DocumentStatus.READY.can_transition_to(DocumentStatus.PROCESSING) is False
        assert DocumentStatus.READY.can_transition_to(DocumentStatus.FAILED) is False
    
    def test_can_transition_from_failed(self):
        """Test valid transitions from FAILED."""
        assert DocumentStatus.FAILED.can_transition_to(DocumentStatus.PROCESSING) is True
        assert DocumentStatus.FAILED.can_transition_to(DocumentStatus.READY) is False


class TestFileType:
    """Tests for FileType value object."""
    
    def test_file_type_values(self):
        """Test all file type values."""
        assert FileType.PDF.value == "pdf"
        assert FileType.DOCX.value == "docx"
        assert FileType.TXT.value == "txt"
        assert FileType.JPG.value == "jpg"
        assert FileType.PNG.value == "png"
    
    def test_from_filename(self):
        """Test extracting file type from filename."""
        assert FileType.from_filename("document.pdf") == FileType.PDF
        assert FileType.from_filename("file.DOCX") == FileType.DOCX
        assert FileType.from_filename("image.PNG") == FileType.PNG
    
    def test_from_filename_invalid(self):
        """Test invalid file type raises error."""
        with pytest.raises(ValueError):
            FileType.from_filename("file.exe")
    
    def test_is_image(self):
        """Test is_image method."""
        assert FileType.JPG.is_image() is True
        assert FileType.JPEG.is_image() is True
        assert FileType.PNG.is_image() is True
        assert FileType.PDF.is_image() is False
    
    def test_is_document(self):
        """Test is_document method."""
        assert FileType.PDF.is_document() is True
        assert FileType.DOCX.is_document() is True
        assert FileType.TXT.is_document() is True
        assert FileType.JPG.is_document() is False


class TestEmbedding:
    """Tests for Embedding value object."""
    
    def test_create_embedding(self):
        """Test creating an embedding."""
        vector = [0.1] * 768
        embedding = Embedding(vector)
        
        assert len(embedding.vector) == 768
    
    def test_embedding_dimension_mismatch(self):
        """Test embedding with wrong dimensions."""
        with pytest.raises(ValueError):
            Embedding([0.1] * 100)  # Wrong dimensions
    
    def test_embedding_vector_property(self):
        """Test getting embedding as list."""
        vector = [0.1] * 768
        embedding = Embedding(vector)
        
        assert isinstance(embedding.vector, list)
        assert len(embedding.vector) == 768
    
    def test_embedding_numpy_array(self):
        """Test getting embedding as numpy array."""
        vector = [0.1] * 768
        embedding = Embedding(vector)
        
        assert isinstance(embedding.numpy_array, np.ndarray)
    
    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical embeddings."""
        vector = [0.1] * 768
        emb1 = Embedding(vector)
        emb2 = Embedding(vector)
        
        similarity = emb1.cosine_similarity(emb2)
        
        assert abs(similarity - 1.0) < 0.001  # Should be ~1.0
    
    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal embeddings."""
        vec1 = [1.0] + [0.0] * 767
        vec2 = [0.0, 1.0] + [0.0] * 766
        
        emb1 = Embedding(vec1)
        emb2 = Embedding(vec2)
        
        similarity = emb1.cosine_similarity(emb2)
        
        assert abs(similarity) < 0.001  # Should be ~0.0
    
    def test_embedding_equality(self):
        """Test embedding equality."""
        vec = [0.1] * 768
        emb1 = Embedding(vec)
        emb2 = Embedding(vec)
        
        assert emb1 == emb2
    
    def test_embedding_repr(self):
        """Test embedding string representation."""
        embedding = Embedding([0.1] * 768)
        
        repr_str = repr(embedding)
        assert "Embedding" in repr_str
        assert "768" in repr_str


# ============================================================
# Domain Exception Tests
# ============================================================

class TestDomainExceptions:
    """Tests for domain exceptions."""
    
    def test_invalid_document_state_error(self):
        """Test InvalidDocumentStateError."""
        with pytest.raises(InvalidDocumentStateError) as exc_info:
            raise InvalidDocumentStateError("Invalid transition")
        
        assert "Invalid transition" in str(exc_info.value)
    
    def test_document_not_found_error(self):
        """Test DocumentNotFoundError."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            raise DocumentNotFoundError("Document 123 not found")
        
        assert "123" in str(exc_info.value)
    
    def test_text_extraction_error(self):
        """Test TextExtractionError."""
        with pytest.raises(TextExtractionError) as exc_info:
            raise TextExtractionError("Failed to extract text")
        
        assert "extract" in str(exc_info.value).lower()
    
    def test_embedding_generation_error(self):
        """Test EmbeddingGenerationError."""
        with pytest.raises(EmbeddingGenerationError) as exc_info:
            raise EmbeddingGenerationError("API error")
        
        assert "API error" in str(exc_info.value)
