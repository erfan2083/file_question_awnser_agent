"""
Comprehensive tests for documents app.
Covers models, views, serializers, and services.
"""

import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from documents.models import Document, DocumentChunk
from documents.serializers import (
    DocumentSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer
)
from documents.services import DocumentProcessor


# ============================================================
# Model Tests
# ============================================================

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
        
        assert document.id is not None
        assert document.title == "Test Document"
        assert document.file_type == "pdf"
        assert document.status == Document.Status.UPLOADED
        assert document.num_chunks == 0
        assert document.num_pages == 0
    
    def test_document_str_representation(self):
        """Test document string representation."""
        document = Document.objects.create(
            title="Test Doc",
            file_type="txt",
            file_size=512,
            status=Document.Status.READY
        )
        
        assert str(document) == "Test Doc (READY)"
    
    def test_document_status_choices(self):
        """Test all document status choices."""
        statuses = [
            Document.Status.UPLOADED,
            Document.Status.PROCESSING,
            Document.Status.READY,
            Document.Status.FAILED
        ]
        
        for status_choice in statuses:
            doc = Document.objects.create(
                title=f"Doc {status_choice}",
                file_type="pdf",
                file_size=100,
                status=status_choice
            )
            assert doc.status == status_choice
    
    def test_document_file_type_choices(self):
        """Test all file type choices."""
        file_types = ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png']
        
        for ft in file_types:
            doc = Document.objects.create(
                title=f"Doc {ft}",
                file_type=ft,
                file_size=100
            )
            assert doc.file_type == ft
    
    def test_document_ordering(self):
        """Test document ordering by created_at descending."""
        doc1 = Document.objects.create(title="Doc 1", file_type="pdf", file_size=100)
        doc2 = Document.objects.create(title="Doc 2", file_type="pdf", file_size=100)
        doc3 = Document.objects.create(title="Doc 3", file_type="pdf", file_size=100)
        
        documents = list(Document.objects.all())
        assert documents[0] == doc3
        assert documents[1] == doc2
        assert documents[2] == doc1
    
    def test_document_with_language(self):
        """Test document with language field."""
        doc = Document.objects.create(
            title="Persian Doc",
            file_type="pdf",
            file_size=100,
            language="fa"
        )
        assert doc.language == "fa"
    
    def test_document_with_error_message(self):
        """Test document with error message."""
        doc = Document.objects.create(
            title="Failed Doc",
            file_type="pdf",
            file_size=100,
            status=Document.Status.FAILED,
            error_message="Processing failed due to corrupt file"
        )
        assert doc.error_message == "Processing failed due to corrupt file"


@pytest.mark.django_db
class TestDocumentChunkModel:
    """Tests for DocumentChunk model."""
    
    def test_create_chunk(self, sample_document):
        """Test creating a document chunk."""
        chunk = DocumentChunk.objects.create(
            document=sample_document,
            index=0,
            text="This is a test chunk",
            embedding=[0.1] * 768,
            char_count=20,
            token_count=5
        )
        
        assert chunk.id is not None
        assert chunk.document == sample_document
        assert chunk.index == 0
        assert chunk.text == "This is a test chunk"
        assert len(chunk.embedding) == 768
    
    def test_chunk_str_representation(self, sample_document):
        """Test chunk string representation."""
        chunk = DocumentChunk.objects.create(
            document=sample_document,
            index=5,
            text="Test chunk",
            embedding=[0.1] * 768
        )
        
        assert str(chunk) == f"{sample_document.title} - Chunk 5"
    
    def test_chunk_ordering(self, sample_document):
        """Test chunk ordering by document and index."""
        chunk2 = DocumentChunk.objects.create(
            document=sample_document,
            index=2,
            text="Chunk 2",
            embedding=[0.1] * 768
        )
        chunk0 = DocumentChunk.objects.create(
            document=sample_document,
            index=0,
            text="Chunk 0",
            embedding=[0.1] * 768
        )
        chunk1 = DocumentChunk.objects.create(
            document=sample_document,
            index=1,
            text="Chunk 1",
            embedding=[0.1] * 768
        )
        
        chunks = list(sample_document.chunks.all())
        assert chunks[0].index == 0
        assert chunks[1].index == 1
        assert chunks[2].index == 2
    
    def test_chunk_unique_together(self, sample_document):
        """Test that document-index combination is unique."""
        DocumentChunk.objects.create(
            document=sample_document,
            index=0,
            text="First chunk",
            embedding=[0.1] * 768
        )
        
        with pytest.raises(Exception):  # IntegrityError
            DocumentChunk.objects.create(
                document=sample_document,
                index=0,  # Same index
                text="Duplicate chunk",
                embedding=[0.1] * 768
            )
    
    def test_chunk_cascade_delete(self, sample_document):
        """Test that chunks are deleted when document is deleted."""
        for i in range(3):
            DocumentChunk.objects.create(
                document=sample_document,
                index=i,
                text=f"Chunk {i}",
                embedding=[0.1] * 768
            )
        
        doc_id = sample_document.id
        sample_document.delete()
        
        assert DocumentChunk.objects.filter(document_id=doc_id).count() == 0


# ============================================================
# Serializer Tests
# ============================================================

@pytest.mark.django_db
class TestDocumentSerializers:
    """Tests for document serializers."""
    
    def test_document_serializer(self, sample_document):
        """Test DocumentSerializer."""
        serializer = DocumentSerializer(sample_document)
        data = serializer.data
        
        assert data['id'] == sample_document.id
        assert data['title'] == sample_document.title
        assert data['file_type'] == sample_document.file_type
        assert data['status'] == sample_document.status
    
    def test_document_detail_serializer_with_chunks(self, sample_document, multiple_chunks):
        """Test DocumentDetailSerializer includes chunks."""
        serializer = DocumentDetailSerializer(sample_document)
        data = serializer.data
        
        assert 'chunks' in data
        assert len(data['chunks']) == 5
    
    def test_document_upload_serializer_valid(self, sample_txt_file):
        """Test DocumentUploadSerializer with valid data."""
        data = {
            'file': sample_txt_file,
            'title': 'Test Upload',
            'language': 'en'
        }
        serializer = DocumentUploadSerializer(data=data)
        assert serializer.is_valid()
    
    def test_document_upload_serializer_invalid_file_type(self):
        """Test DocumentUploadSerializer rejects invalid file types."""
        invalid_file = SimpleUploadedFile(
            name="test.exe",
            content=b"executable content",
            content_type="application/octet-stream"
        )
        data = {'file': invalid_file}
        serializer = DocumentUploadSerializer(data=data)
        assert not serializer.is_valid()
        assert 'file' in serializer.errors
    
    def test_document_chunk_serializer(self, sample_chunk):
        """Test DocumentChunkSerializer."""
        serializer = DocumentChunkSerializer(sample_chunk)
        data = serializer.data
        
        assert data['id'] == sample_chunk.id
        assert data['index'] == sample_chunk.index
        assert data['text'] == sample_chunk.text
        assert 'embedding' not in data  # Should not expose embedding


# ============================================================
# View Tests
# ============================================================

@pytest.mark.django_db
class TestDocumentViews:
    """Tests for document views."""
    
    def test_list_documents(self, api_client, sample_document):
        """Test listing documents."""
        response = api_client.get('/api/documents/')
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        data = response.json()
        if 'results' in data:
            assert len(data['results']) >= 1
        else:
            assert len(data) >= 1
    
    def test_retrieve_document(self, api_client, sample_document):
        """Test retrieving a single document."""
        response = api_client.get(f'/api/documents/{sample_document.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['title'] == sample_document.title
    
    def test_retrieve_document_not_found(self, api_client):
        """Test retrieving non-existent document."""
        response = api_client.get('/api/documents/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_document(self, api_client, sample_document):
        """Test deleting a document."""
        doc_id = sample_document.id
        response = api_client.delete(f'/api/documents/{doc_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=doc_id).exists()
    
    @patch('documents.views.DocumentProcessor')
    def test_upload_document(self, mock_processor, api_client, sample_txt_file):
        """Test uploading a document."""
        mock_processor.return_value.process_document.return_value = True
        
        response = api_client.post(
            '/api/documents/upload/',
            {'file': sample_txt_file, 'title': 'Test Upload'},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['title'] == 'Test Upload'
        assert data['file_type'] == 'txt'
    
    @patch('documents.views.DocumentProcessor')
    def test_reprocess_failed_document(self, mock_processor, api_client, sample_document_failed):
        """Test reprocessing a failed document."""
        mock_processor.return_value.process_document.return_value = True
        
        response = api_client.post(
            f'/api/documents/{sample_document_failed.id}/reprocess/'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_reprocess_ready_document_fails(self, api_client, sample_document):
        """Test that reprocessing a ready document fails."""
        response = api_client.post(
            f'/api/documents/{sample_document.id}/reprocess/'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDocumentChunkViews:
    """Tests for document chunk views."""
    
    def test_list_chunks(self, api_client, sample_chunk):
        """Test listing chunks."""
        response = api_client.get('/api/documents/chunks/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_chunks_by_document(self, api_client, sample_document, multiple_chunks):
        """Test filtering chunks by document ID."""
        response = api_client.get(
            f'/api/documents/chunks/?document_id={sample_document.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if 'results' in data:
            assert len(data['results']) == 5
        else:
            assert len(data) == 5


# ============================================================
# Service Tests
# ============================================================

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
        
        # Create long text
        text = "This is a test sentence. " * 200
        chunks = processor._chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_short(self):
        """Test chunking short text."""
        processor = DocumentProcessor()
        
        text = "Short text."
        chunks = processor._chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == "Short text."
    
    @patch('documents.services.genai.embed_content')
    def test_generate_embedding(self, mock_embed, sample_document_uploaded):
        """Test embedding generation."""
        mock_embed.return_value = {'embedding': [0.1] * 768}
        
        processor = DocumentProcessor()
        embedding = processor._generate_embedding("Test text")
        
        assert len(embedding) == 768
        mock_embed.assert_called_once()
    
    def test_extract_from_txt(self, tmp_path):
        """Test text extraction from TXT file."""
        # Create a temp text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is test content.\nSecond line.")
        
        processor = DocumentProcessor()
        text, num_pages = processor._extract_from_txt(str(txt_file))
        
        assert "This is test content." in text
        assert "Second line." in text
        assert num_pages >= 1
