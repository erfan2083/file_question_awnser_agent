"""
Tests for documents app.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, DocumentChunk
from documents.services import DocumentProcessor


@pytest.mark.django_db
class TestDocumentModel:
    """Tests for Document model."""
    
    def test_create_document(self):
        """Test creating a document."""
        document = Document.objects.create(
            title="Test Document",
            file_type="pdf",
            file_size=1024,
            status=Document.Status.UPLOADED
        )
        
        assert document.title == "Test Document"
        assert document.file_type == "pdf"
        assert document.status == Document.Status.UPLOADED
        assert document.num_chunks == 0
    
    def test_document_str(self):
        """Test document string representation."""
        document = Document.objects.create(
            title="Test Doc",
            file_type="txt",
            file_size=512,
            status=Document.Status.READY
        )
        
        assert str(document) == "Test Doc (READY)"


@pytest.mark.django_db
class TestDocumentChunk:
    """Tests for DocumentChunk model."""
    
    def test_create_chunk(self):
        """Test creating a document chunk."""
        document = Document.objects.create(
            title="Test Document",
            file_type="txt",
            file_size=1024
        )
        
        chunk = DocumentChunk.objects.create(
            document=document,
            index=0,
            text="This is a test chunk",
            embedding=[0.1] * 768,  # Mock embedding
            char_count=20,
            token_count=5
        )
        
        assert chunk.document == document
        assert chunk.index == 0
        assert chunk.text == "This is a test chunk"
        assert len(chunk.embedding) == 768


@pytest.mark.django_db
class TestDocumentProcessor:
    """Tests for DocumentProcessor service."""
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = DocumentProcessor()
        
        assert processor.chunk_size > 0
        assert processor.chunk_overlap > 0
        assert processor.text_splitter is not None
    
    def test_chunk_text(self):
        """Test text chunking."""
        processor = DocumentProcessor()
        
        text = "This is a test sentence. " * 100  # Long text
        chunks = processor._chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)


@pytest.mark.django_db  
class TestDocumentViews:
    """Tests for document views."""
    
    def test_document_list(self, client):
        """Test listing documents."""
        # Create test documents
        Document.objects.create(
            title="Doc 1",
            file_type="pdf",
            file_size=1024
        )
        Document.objects.create(
            title="Doc 2",
            file_type="txt",
            file_size=512
        )
        
        response = client.get('/api/documents/')
        
        assert response.status_code == 200
        assert len(response.json()) >= 2
    
    def test_document_detail(self, client):
        """Test retrieving document detail."""
        document = Document.objects.create(
            title="Test Doc",
            file_type="pdf",
            file_size=1024
        )
        
        response = client.get(f'/api/documents/{document.id}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == "Test Doc"
        assert data['file_type'] == "pdf"


# Fixtures
@pytest.fixture
def sample_document(db):
    """Fixture for creating a sample document."""
    return Document.objects.create(
        title="Sample Document",
        file_type="txt",
        file_size=1024,
        status=Document.Status.READY
    )


@pytest.fixture
def sample_chunk(sample_document):
    """Fixture for creating a sample chunk."""
    return DocumentChunk.objects.create(
        document=sample_document,
        index=0,
        text="Sample chunk text",
        embedding=[0.1] * 768,
        char_count=17,
        token_count=3
    )
