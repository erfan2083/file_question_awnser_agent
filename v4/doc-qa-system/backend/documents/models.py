from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    """Model for uploaded documents"""

    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        PROCESSING = "PROCESSING", "Processing"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Failed"

    class FileType(models.TextChoices):
        PDF = "PDF", "PDF"
        DOCX = "DOCX", "DOCX"
        TXT = "TXT", "TXT"
        JPG = "JPG", "JPG"
        PNG = "PNG", "PNG"

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    language = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPLOADED
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class DocumentChunk(models.Model):
    """Model for document text chunks with embeddings"""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    index = models.IntegerField()
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "index"]
        unique_together = ["document", "index"]
        indexes = [
            models.Index(fields=["document", "index"]),
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.index}"
