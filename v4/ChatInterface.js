import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../services/api';
import './ChatInterface.css';

const ChatInterface = ({ sessionId: propSessionId }) => {
  const [sessionId, setSessionId] = useState(propSessionId);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!sessionId) {
      createSession();
    } else {
      loadMessages();
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const createSession = async () => {
    try {
      const response = await chatAPI.createSession();
      setSessionId(response.data.id);
    } catch (err) {
      console.error('Error creating session:', err);
    }
  };

  const loadMessages = async () => {
    try {
      const response = await chatAPI.getMessages(sessionId);
      setMessages(response.data);
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(sessionId, input);

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        citations: response.data.citations || [],
        intent: response.data.intent,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Document Q&A Assistant</h2>
        <p>Ask questions about your documents or use commands like "summarize", "translate", or "create checklist"</p>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Welcome! 👋</h3>
            <p>Upload documents and start asking questions.</p>
            <div className="example-queries">
              <p><strong>Example queries:</strong></p>
              <ul>
                <li>What is this document about?</li>
                <li>Summarize the main points</li>
                <li>Translate this to Persian / به فارسی ترجمه کن</li>
                <li>Create a checklist from this</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <div className="message-text">{msg.content}</div>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations">
                    <strong>Sources:</strong>
                    {msg.citations.map((citation, cidx) => (
                      <div key={cidx} className="citation">
                        <span className="citation-doc">
                          📄 {citation.document_title}
                        </span>
                        <span className="citation-page">
                          Page {citation.page}
                        </span>
                        <div className="citation-snippet">
                          {citation.snippet}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="message-time">
                {new Date(msg.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question or give a command... (Shift+Enter for new line)"
          rows="3"
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
