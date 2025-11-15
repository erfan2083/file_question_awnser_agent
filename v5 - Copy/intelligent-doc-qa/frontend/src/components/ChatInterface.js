import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { chatApi } from '../services/api';
import './ChatInterface.css';

const ChatInterface = () => {
  const [sessionId, setSessionId] = useState(null);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);
  const queryClient = useQueryClient();
  
  // Create or get session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await chatApi.listSessions();
        if (response.data && response.data.length > 0) {
          // Use existing session
          setSessionId(response.data[0].id);
        } else {
          // Create new session
          const newSession = await chatApi.createSession({ title: 'Chat Session' });
          setSessionId(newSession.data.id);
        }
      } catch (error) {
        console.error('Error initializing session:', error);
      }
    };
    
    initSession();
  }, []);
  
  // Fetch messages when session is set
  useEffect(() => {
    if (sessionId) {
      const fetchMessages = async () => {
        try {
          const response = await chatApi.getMessages(sessionId);
          setMessages(response.data);
        } catch (error) {
          console.error('Error fetching messages:', error);
        }
      };
      
      fetchMessages();
    }
  }, [sessionId]);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Send message mutation
  const sendMessageMutation = useMutation(
    (content) => chatApi.sendMessage(sessionId, content),
    {
      onSuccess: (response) => {
        // Add user message
        const userMessage = {
          role: 'user',
          content: message,
          created_at: new Date().toISOString(),
        };
        
        // Add assistant message
        const assistantMessage = {
          role: 'assistant',
          content: response.data.answer,
          metadata: {
            citations: response.data.citations,
            ...response.data.metadata,
          },
          created_at: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, userMessage, assistantMessage]);
        setMessage('');
      },
      onError: (error) => {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
      },
    }
  );
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!message.trim() || !sessionId) return;
    
    sendMessageMutation.mutate(message);
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const renderMessage = (msg, index) => {
    const isUser = msg.role === 'user';
    
    return (
      <div key={index} className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
        <div className="message-content">
          <div className="message-text">{msg.content}</div>
          
          {/* Render citations for assistant messages */}
          {!isUser && msg.metadata?.citations && msg.metadata.citations.length > 0 && (
            <div className="citations">
              <div className="citations-title">📚 Sources:</div>
              {msg.metadata.citations.map((citation, idx) => (
                <div key={idx} className="citation-item">
                  <strong>{citation.document_title}</strong>
                  {citation.page && ` (Page ${citation.page})`}
                  <div className="citation-snippet">{citation.snippet}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="message-timestamp">
          {new Date(msg.created_at).toLocaleTimeString()}
        </div>
      </div>
    );
  };
  
  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>💬 Chat</h2>
        <p>Ask questions about your documents (English or Persian)</p>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Welcome! 👋</h3>
            <p>Upload some documents and start asking questions.</p>
            <p>You can also use utility commands like:</p>
            <ul>
              <li>"Summarize this document"</li>
              <li>"Translate to Persian / به فارسی ترجمه کن"</li>
              <li>"Create a checklist / چک‌لیست بساز"</li>
            </ul>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => renderMessage(msg, idx))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your question here... (Shift+Enter for new line)"
          rows={3}
          disabled={!sessionId || sendMessageMutation.isLoading}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!message.trim() || !sessionId || sendMessageMutation.isLoading}
        >
          {sendMessageMutation.isLoading ? '⏳' : '📤'} Send
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
