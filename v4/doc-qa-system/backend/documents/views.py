from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage
from .models import Document
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer,
)
from .services import DocumentIngestionService
import os
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for document operations"""

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_serializer_class(self):
        if self.action == "upload":
            return DocumentUploadSerializer
        return DocumentSerializer

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Upload and process a document"""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]

        # Determine file type
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_type_map = {
            ".pdf": Document.FileType.PDF,
            ".docx": Document.FileType.DOCX,
            ".txt": Document.FileType.TXT,
            ".jpg": Document.FileType.JPG,
            ".jpeg": Document.FileType.JPG,
            ".png": Document.FileType.PNG,
        }
        file_type = file_type_map.get(file_ext, Document.FileType.TXT)

        # Create document record
        document = Document.objects.create(
            title=uploaded_file.name,
            file=uploaded_file,
            file_type=file_type,
            status=Document.Status.UPLOADED,
        )

        # Process document asynchronously (in production, use Celery)
        try:
            ingestion_service = DocumentIngestionService()
            ingestion_service.process_document(document)
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="chunks")
    def chunks(self, request, pk=None):
        """Get chunks for a document"""
        document = self.get_object()
        chunks = document.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)
