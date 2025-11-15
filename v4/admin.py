from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "created_at", "updated_at"]
    search_fields = ["title"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "role", "created_at"]
    list_filter = ["role", "session"]
    search_fields = ["content"]
    readonly_fields = ["created_at"]
