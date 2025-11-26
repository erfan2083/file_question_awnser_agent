"""
Models for document management and storage.
"""

from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    """Model for storing uploaded documents."""
    
    class Status(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        PROCESSING = 'PROCESSING', 'Processing'
        READY = 'READY', 'Ready'
        FAILED = 'FAILED', 'Failed'
    
    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'
        TXT = 'txt', 'TXT'
        JPG = 'jpg', 'JPG'
        JPEG = 'jpeg', 'JPEG'
        PNG = 'png', 'PNG'
    
    title = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    language = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED
    )
    error_message = models.TextField(blank=True, null=True)
    
    # Metadata
    num_chunks = models.IntegerField(default=0)
    num_pages = models.IntegerField(default=0, help_text="Number of pages (if applicable)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class DocumentChunk(models.Model):
    """Model for storing document chunks with embeddings."""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    index = models.IntegerField(help_text="Chunk index within the document")
    text = models.TextField(help_text="Chunk text content")
    page_number = models.IntegerField(
        blank=True,
        null=True,
        help_text="Page number if applicable"
    )
    
    # Vector embedding (768 dimensions for Gemini embeddings)
    embedding = VectorField(dimensions=768)
    
    # Metadata for better retrieval
    char_count = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'index']
        indexes = [
            models.Index(fields=['document', 'index']),
        ]
        unique_together = ['document', 'index']
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.index}"
