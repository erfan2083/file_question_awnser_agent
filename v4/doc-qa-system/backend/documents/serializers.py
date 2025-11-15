from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for document chunks"""

    class Meta:
        model = DocumentChunk
        fields = ["id", "index", "text", "page_number", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents"""

    chunks_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file",
            "file_type",
            "language",
            "status",
            "error_message",
            "chunks_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "error_message", "created_at", "updated_at"]

    def get_chunks_count(self, obj):
        return obj.chunks.count()


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""

    file = serializers.FileField()

    def validate_file(self, value):
        """Validate file type"""
        allowed_extensions = [".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"]
        file_name = value.name.lower()

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )

        return value
