"""
Views for documents app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction

from documents.models import Document, DocumentChunk
from documents.serializers import (
    DocumentSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer
)
from documents.services import DocumentProcessor


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for document management."""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        elif self.action == 'upload':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Upload a new document.
        
        Accepts multipart/form-data with:
        - file: The document file
        - title: Optional title (defaults to filename)
        - language: Optional language code
        """
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        title = serializer.validated_data.get('title', uploaded_file.name)
        language = serializer.validated_data.get('language', '')
        
        # Get file extension
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # Create document record
        document = Document.objects.create(
            title=title,
            file_path=uploaded_file,
            file_type=file_ext,
            file_size=uploaded_file.size,
            language=language,
            status=Document.Status.UPLOADED
        )
        
        # Process document asynchronously (in production, use Celery)
        # For now, process synchronously
        try:
            processor = DocumentProcessor()
            processor.process_document(document)
        except Exception as e:
            # If processing fails immediately, update status
            document.status = Document.Status.FAILED
            document.error_message = str(e)
            document.save()
        
        # Return created document
        response_serializer = DocumentSerializer(document)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, pk=None):
        """Reprocess a failed document."""
        document = self.get_object()
        
        if document.status != Document.Status.FAILED:
            return Response(
                {'error': 'Only failed documents can be reprocessed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status
        document.status = Document.Status.UPLOADED
        document.error_message = None
        document.save()
        
        # Process document
        try:
            processor = DocumentProcessor()
            processor.process_document(document)
        except Exception as e:
            document.status = Document.Status.FAILED
            document.error_message = str(e)
            document.save()
        
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="utility")
    def utility(self, request, pk=None):
        """
        Run a utility action (summarize, translate, checklist) on a document.

        Accepts JSON body with:
        - action: One of "summarize", "translate", "checklist"
        """
        document = self.get_object()

        if document.status != Document.Status.READY:
            return Response(
                {"error": "Document is not ready for processing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action_name = request.data.get("action", "").strip().lower()
        if action_name not in ("summarize", "translate", "checklist"):
            return Response(
                {
                    "error": (
                        f"Invalid action '{action_name}'. "
                        "Must be one of: summarize, translate, checklist."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from rag.services import RAGOrchestrator

        orchestrator = RAGOrchestrator()
        result = orchestrator.process_document_utility(
            document_id=document.id,
            action=action_name,
        )

        if result.get("error"):
            return Response(
                {"error": result["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "document_id": document.id,
                "document_title": document.title,
                "action": action_name,
                "answer": result["answer"],
                "metadata": result.get("metadata", {}),
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a document and its chunks."""
        document = self.get_object()
        
        # Delete file from storage
        if document.file_path:
            document.file_path.delete()
        
        # Delete document (chunks will cascade)
        document.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for document chunks."""
    
    queryset = DocumentChunk.objects.all()
    serializer_class = DocumentChunkSerializer
    
    def get_queryset(self):
        """Filter chunks by document if provided."""
        queryset = super().get_queryset()
        document_id = self.request.query_params.get('document_id')
        
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        return queryset
