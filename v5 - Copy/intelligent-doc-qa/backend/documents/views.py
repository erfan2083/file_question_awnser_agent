"""
Views for documents app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction

from documents.models import Document, DocumentChunk
from documents.serializers import (
    DocumentSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer
)
# We no longer need DocumentProcessor here, but we need the task
from documents.tasks import process_document_task


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for document management."""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        elif self.action == 'upload':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        title = serializer.validated_data.get('title', uploaded_file.name)
        language = serializer.validated_data.get('language', '')
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        document = Document.objects.create(
            title=title,
            file_path=uploaded_file,
            file_type=file_ext,
            file_size=uploaded_file.size,
            language=language,
            status=Document.Status.UPLOADED
        )
        
        # -----------------------------------------------------------------
        # OLD SYNCHRONOUS CODE (REMOVED)
        # try:
        #     processor = DocumentProcessor()
        #     processor.process_document(document)
        # except Exception as e:
        #     document.status = Document.Status.FAILED
        #     document.error_message = str(e)
        #     document.save()
        
        # NEW ASYNCHRONOUS CODE
        process_document_task.delay(document.id)
        # -----------------------------------------------------------------
        
        response_serializer = DocumentSerializer(document)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, pk=None):
        document = self.get_object()
        
        if document.status != Document.Status.FAILED:
            return Response(
                {'error': 'Only failed documents can be reprocessed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status and trigger async task
        document.status = Document.Status.UPLOADED
        document.error_message = None
        document.save()
        
        # -----------------------------------------------------------------
        # OLD SYNCHRONOUS CODE (REMOVED)
        # try:
        #     processor = DocumentProcessor()
        #     processor.process_document(document)
        # except Exception as e:
        #     document.status = Document.Status.FAILED
        #     document.error_message = str(e)
        #     document.save()

        # NEW ASYNCHRONOUS CODE
        process_document_task.delay(document.id)
        # -----------------------------------------------------------------
        
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    
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
