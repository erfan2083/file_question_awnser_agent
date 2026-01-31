import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import './App.css';

const queryClient = new QueryClient();

function App() {
  const [utilityResult, setUtilityResult] = useState(null);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <header className="App-header">
          <h1>Intelligent Document QA System</h1>
          <p>Upload documents and ask questions in English or Persian</p>
        </header>

        <div className="main-container">
          <aside className="sidebar">
            <DocumentList onUtilityResult={setUtilityResult} />
          </aside>

          <main className="chat-container">
            <ChatInterface utilityResult={utilityResult} onUtilityConsumed={() => setUtilityResult(null)} />
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
