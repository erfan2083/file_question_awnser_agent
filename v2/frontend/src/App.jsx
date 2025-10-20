import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ChatInterface from './components/ChatInterface'
import { FaBook, FaComments } from 'react-icons/fa'
import './App.css' // We'll create this for layout

function App() {
  // This state tracks if documents are ready for querying.
  const [docsReady, setDocsReady] = useState(false)
  
  // This state is just to show a "processing" message.
  const [isProcessing, setIsProcessing] = useState(false)

  const handleUploadSuccess = () => {
    setDocsReady(true)
    setIsProcessing(false)
  }
  
  const handleUploadStart = () => {
    setIsProcessing(true)
    setDocsReady(false)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Local Hybrid RAG 🤖</h1>
        <p>Upload documents and ask questions.</p>
      </header>

      <main className="app-main">
        <div className="main-column upload-column">
          <h2><FaBook /> 1. Upload Documents</h2>
          <FileUpload 
            onUploadStart={handleUploadStart}
            onUploadSuccess={handleUploadSuccess} 
          />
        </div>
        
        <div className="main-column chat-column">
           <h2><FaComments /> 2. Ask a Question</h2>
          <ChatInterface 
            isEnabled={docsReady} 
            isProcessing={isProcessing}
          />
        </div>
      </main>
    </div>
  )
}

// Create a new CSS file for App layout
// `frontend/src/App.css`
/*
.app-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.app-main {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.main-column {
  background-color: var(--bg-color-dark);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  min-height: 400px;
}

.main-column h2 {
  margin-top: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f9f9f9;
}

@media (min-width: 900px) {
  .app-main {
    grid-template-columns: 1fr 2fr;
  }
}

@media (prefers-color-scheme: light) {
  .main-column h2 {
    color: #213547;
  }
}
*/
export default App