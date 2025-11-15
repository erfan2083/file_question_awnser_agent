from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""

    citations = serializers.SerializerMethodField()
    intent = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "role",
            "content",
            "citations",
            "intent",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_citations(self, obj):
        return obj.get_citations()

    def get_intent(self, obj):
        return obj.get_intent()


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions"""

    messages_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "messages_count",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                "role": last_msg.role,
                "content": last_msg.content[:100] + "..."
                if len(last_msg.content) > 100
                else last_msg.content,
                "created_at": last_msg.created_at,
            }
        return None


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message"""

    content = serializers.CharField()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()
