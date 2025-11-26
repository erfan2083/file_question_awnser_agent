"""
Serializers for chat app.
"""

from rest_framework import serializers
from chat.models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'session', 'role', 'content',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""
    
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'messages', 'message_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """Get total message count for the session."""
        return obj.messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sessions."""
    
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'created_at', 'updated_at',
            'message_count', 'last_message'
        ]
        read_only_fields = fields
    
    def get_message_count(self, obj):
        """Get total message count."""
        return obj.messages.count()
    
    def get_last_message(self, obj):
        """Get preview of last message."""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message."""
    
    content = serializers.CharField()


class MessageResponseSerializer(serializers.Serializer):
    """Serializer for message response with answer and citations."""
    
    answer = serializers.CharField()
    citations = serializers.ListField()
    session_id = serializers.IntegerField()
    message_id = serializers.IntegerField()
    metadata = serializers.DictField()
