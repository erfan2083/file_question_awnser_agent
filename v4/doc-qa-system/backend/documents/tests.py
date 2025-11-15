import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, DocumentChunk
from documents.services import DocumentIngestionService
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestDocumentModel:
    """Tests for Document model"""

    def test_create_document(self):
        doc = Document.objects.create(
            title="Test Doc",
            file=SimpleUploadedFile("test.pdf", b"content"),
            file_type=Document.FileType.PDF,
        )
        assert doc.title == "Test Doc"
        assert doc.status == Document.Status.UPLOADED
        assert str(doc) == "Test Doc (UPLOADED)"

    def test_document_status_transition(self, sample_document):
        sample_document.status = Document.Status.PROCESSING
        sample_document.save()
        assert sample_document.status == Document.Status.PROCESSING


@pytest.mark.django_db
class TestDocumentChunk:
    """Tests for DocumentChunk model"""

    def test_create_chunk(self, sample_document):
        chunk = DocumentChunk.objects.create(
            document=sample_document,
            index=0,
            text="Test text",
            page_number=1,
        )
        assert chunk.document == sample_document
        assert chunk.index == 0


@pytest.mark.django_db
class TestDocumentAPI:
    """Tests for Document API endpoints"""

    def test_list_documents(self, sample_document):
        client = APIClient()
        response = client.get("/api/documents/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_get_document_detail(self, sample_document):
        client = APIClient()
        response = client.get(f"/api/documents/{sample_document.id}/")
        assert response.status_code == 200
        assert response.data["title"] == sample_document.title

    def test_upload_document(self):
        client = APIClient()
        file_content = b"Test document content"
        file = SimpleUploadedFile("test.txt", file_content)

        response = client.post(
            "/api/documents/upload/", {"file": file}, format="multipart"
        )
        assert response.status_code == 201
        assert "id" in response.data


@pytest.mark.django_db
class TestDocumentIngestionService:
    """Tests for DocumentIngestionService"""

    def test_extract_from_txt(self, tmp_path):
        service = DocumentIngestionService()

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for ingestion")

        text, page_info = service._extract_from_txt(str(test_file))
        assert "Test content" in text
        assert len(page_info) > 0

    def test_create_chunks(self):
        service = DocumentIngestionService()
        text = " ".join(["word"] * 1000)
        page_info = [1] * 1000

        chunks = service._create_chunks(text, page_info)
        assert len(chunks) > 0
        assert all(isinstance(chunk, tuple) for chunk in chunks)
