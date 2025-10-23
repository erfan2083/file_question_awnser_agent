import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FaPaperPlane, FaUser, FaRobot, FaBookOpen, FaExclamationTriangle } from 'react-icons/fa'
import './ChatInterface.css' // Create this file

const ChatInterface = ({ isEnabled, isProcessing }) => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSend = async () => {
    if (!input || !isEnabled || isLoading) return

    const userMessage = { sender: 'user', text: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Add a "thinking" message
      setMessages(prev => [
        ...prev, 
        { sender: 'bot', text: 'Thinking...', sources: [], isLoading: true }
      ])

      const response = await axios.post('/api/v1/query', { query: input })
      
      const botMessage = {
        sender: 'bot',
        text: response.data.answer,
        sources: response.data.sources,
      }
      
      // Replace the "thinking" message with the real answer
      setMessages(prev => [...prev.slice(0, -1), botMessage])

    } catch (err) {
      console.error(err)
      const errorMsg = {
        sender: 'bot',
        text: err.response?.data?.detail || 'An error occurred. Please try again.',
        sources: [],
        isError: true,
      }
      // Replace the "thinking" message with the error
      setMessages(prev => [...prev.slice(0, -1), errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const getDisabledMessage = () => {
    if (isProcessing) {
      return "Processing documents... Please wait."
    }
    if (!isEnabled) {
      return "Please upload documents to begin chatting."
    }
    return null
  }
  
  const disabledMessage = getDisabledMessage()

  return (
    <div className="chat-container">
      {disabledMessage && (
        <div className="chat-overlay">
          <p>{disabledMessage}</p>
        </div>
      )}

      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-icon">
              {msg.sender === 'user' ? <FaUser /> : (msg.isError ? <FaExclamationTriangle /> : <FaRobot />)}
            </div>
            <div className="message-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.text}
              </ReactMarkdown>
              
              {!msg.isLoading && msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <strong><FaBookOpen /> Sources:</strong>
                  <ul>
                    {msg.sources.map((src, i) => (
                      <li key={i}>
                        {src.filename} {src.page ? `(Page ${src.page})` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isEnabled ? "Ask a question..." : ""}
          rows="1"
          disabled={!isEnabled || isLoading}
        />
        <button onClick={handleSend} disabled={!isEnabled || isLoading || !input}>
          <FaPaperPlane />
        </button>
      </div>
    </div>
  )
}


export default ChatInterface