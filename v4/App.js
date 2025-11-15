import React, { useState } from 'react';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [selectedDocument, setSelectedDocument] = useState(null);

  return (
    <div className="app">
      <header className="app-header">
        <h1>📚 Intelligent Document Q&A System</h1>
        <p>Multi-Agent RAG with LangChain & LangGraph</p>
      </header>

      <div className="app-content">
        <aside className="sidebar">
          <DocumentList onDocumentClick={setSelectedDocument} />
        </aside>

        <main className="main-panel">
          <ChatInterface />
        </main>
      </div>
    </div>
  );
}

export default App;
