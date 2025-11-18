"""
Views for chat app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from chat.models import ChatSession, ChatMessage
from chat.serializers import (
    ChatSessionSerializer,
    ChatSessionListSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
    MessageResponseSerializer
)
from rag.services import RAGOrchestrator


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat session management."""
    
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer
    
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        Handle messages for a session.
        GET: Retrieve all messages.
        POST: Send a new message and get a response.
        """
        session = self.get_object()

        # Handle POST (Send Message)
        if request.method == 'POST':
            # Validate input
            input_serializer = SendMessageSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)
            
            user_content = input_serializer.validated_data['content']
            
            # Create user message
            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.USER,
                content=user_content
            )
            
            # Get conversation history (last 5 messages for context)
            # Note: This includes the message we just created
            history_messages = session.messages.order_by('-created_at')[:5]
            chat_history = [
                {
                    'role': msg.role,
                    'content': msg.content
                }
                for msg in reversed(list(history_messages))
            ]
            
            # Process query through RAG orchestrator
            orchestrator = RAGOrchestrator()
            result = orchestrator.process_query(
                query=user_content,
                chat_history=chat_history
            )
            
            # Handle errors
            if result.get('error'):
                assistant_content = (
                    "I apologize, but I encountered an error while processing your request. "
                    "Please try again or rephrase your question."
                )
                metadata = {'error': result['error']}
                citations = []
            else:
                assistant_content = result['answer']
                citations = result['citations']
                metadata = result['metadata']
                metadata['citations'] = citations
            
            # Create assistant message
            assistant_message = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=assistant_content,
                metadata=metadata
            )
            
            # Prepare response
            response_data = {
                'answer': assistant_content,
                'citations': citations,
                'session_id': session.id,
                'message_id': assistant_message.id,
                'metadata': metadata
            }
            
            response_serializer = MessageResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # Handle GET (List Messages)
        messages = session.messages.all().order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], url_path='clear')
    def clear_messages(self, request, pk=None):
        """Clear all messages in a session."""
        session = self.get_object()
        session.messages.all().delete()
        return Response(
            {'message': 'All messages cleared'},
            status=status.HTTP_200_OK
        )


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for chat messages."""
    
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    
    def get_queryset(self):
        """Filter messages by session if provided."""
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset.order_by('created_at')