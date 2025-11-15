"""
Serializers for documents app.
"""

from rest_framework import serializers
from documents.models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for document chunks."""
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'index', 'text', 'page_number',
            'char_count', 'token_count', 'created_at'
        ]
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents."""
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file_path', 'file_type', 'file_size',
            'language', 'status', 'error_message', 'num_chunks',
            'num_pages', 'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'status', 'error_message',
            'num_chunks', 'num_pages', 'created_at',
            'updated_at', 'processed_at'
        ]


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""
    
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False)
    language = serializers.CharField(max_length=10, required=False)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Get file extension
        file_ext = value.name.split('.')[-1].lower()
        
        from django.conf import settings
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise serializers.ValidationError(
                f"File type '{file_ext}' not supported. "
                f"Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        return value


class DocumentDetailSerializer(DocumentSerializer):
    """Detailed serializer for documents with chunks."""
    
    chunks = DocumentChunkSerializer(many=True, read_only=True)
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ['chunks']
