from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)
from rag.retrieval import RetrievalService
from rag.agents import MultiAgentOrchestrator
import logging

logger = logging.getLogger(__name__)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat sessions"""

    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        """Get all messages for a session"""
        session = self.get_object()
        messages = session.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="messages")
    def send_message(self, request, pk=None):
        """Send a message and get AI response"""
        session = self.get_object()

        # Validate input
        message_serializer = SendMessageSerializer(data=request.data)
        message_serializer.is_valid(raise_exception=True)

        user_content = message_serializer.validated_data["content"]

        # Create user message
        user_message = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=user_content
        )

        # Get conversation history
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages.all().order_by("created_at")[-10:]
        ]

        # Process query with multi-agent system
        try:
            retrieval_service = RetrievalService()
            orchestrator = MultiAgentOrchestrator(retrieval_service)

            result = orchestrator.process_query(user_content, conversation_history)

            # Create assistant message
            assistant_message = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=result["answer"],
                metadata={
                    "citations": result["citations"],
                    "intent": result["intent"],
                    **result.get("metadata", {}),
                },
            )

            # Update session title if it's the first message
            if session.messages.count() == 2 and not session.title:
                session.title = user_content[:50] + (
                    "..." if len(user_content) > 50 else ""
                )
                session.save()

            return Response(
                {
                    "answer": result["answer"],
                    "citations": result["citations"],
                    "session_id": session.id,
                    "message_id": assistant_message.id,
                    "intent": result["intent"],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return Response(
                {"error": "An error occurred processing your message"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
