from django.db import models
import json


class ChatSession(models.Model):
    """Model for chat sessions"""

    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.id} - {self.title or 'Untitled'}"


class ChatMessage(models.Model):
    """Model for chat messages"""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    def get_citations(self):
        """Get citations from metadata"""
        return self.metadata.get("citations", [])

    def get_intent(self):
        """Get intent from metadata"""
        return self.metadata.get("intent", "")
