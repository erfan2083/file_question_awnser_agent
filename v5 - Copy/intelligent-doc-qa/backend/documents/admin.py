from django.contrib import admin
from documents.models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'status', 'num_chunks', 'created_at']
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'index', 'page_number', 'char_count', 'created_at']
    list_filter = ['document', 'created_at']
    search_fields = ['text']
    readonly_fields = ['created_at']
