from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "file_type", "status", "created_at"]
    list_filter = ["status", "file_type"]
    search_fields = ["title"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "index", "page_number", "created_at"]
    list_filter = ["document"]
    search_fields = ["text"]
    readonly_fields = ["created_at"]
