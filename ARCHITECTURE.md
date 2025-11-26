# System Architecture Documentation

## High-Level Architecture

The Intelligent Document QA System follows a three-tier architecture:

1. **Presentation Layer** (React Frontend)
2. **Application Layer** (Django Backend with LangGraph)
3. **Data Layer** (PostgreSQL with pgvector)

## Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │             React SPA (Port 3000)                        │  │
│  │                                                          │  │
│  │  ┌─────────────┐           ┌──────────────┐            │  │
│  │  │  Document   │           │    Chat      │            │  │
│  │  │    List     │           │  Interface   │            │  │
│  │  │  Component  │           │  Component   │            │  │
│  │  └─────────────┘           └──────────────┘            │  │
│  │         │                          │                    │  │
│  │         └──────────┬───────────────┘                    │  │
│  │                    │                                    │  │
│  │             ┌──────▼─────┐                              │  │
│  │             │   API      │                              │  │
│  │             │  Service   │                              │  │
│  │             │  (Axios)   │                              │  │
│  │             └────────────┘                              │  │
│  └──────────────────┬──────────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────────┘
                      │ HTTP/REST API
                      │ JSON
┌─────────────────────▼──────────────────────────────────────────┐
│                   BACKEND SERVER                                │
│               Django + DRF (Port 8000)                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  REST API Layer                           │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐           │  │
│  │  │Documents │  │   Chat   │  │ Evaluation   │           │  │
│  │  │   API    │  │   API    │  │     API      │           │  │
│  │  └────┬─────┘  └────┬─────┘  └──────┬───────┘           │  │
│  └───────┼─────────────┼────────────────┼──────────────────┘  │
│          │             │                │                     │
│  ┌───────▼─────────────▼────────────────▼──────────────────┐  │
│  │              Business Logic Layer                        │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         Document Processing Service             │  │  │
│  │  │  - Text Extraction (PDF, DOCX, TXT)            │  │  │
│  │  │  - OCR (Images via Google Vision)              │  │  │
│  │  │  - Text Chunking (LangChain)                   │  │  │
│  │  │  - Embedding Generation (Gemini)               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │      RAG Orchestration Service (LangGraph)      │  │  │
│  │  │                                                     │  │  │
│  │  │   ┌──────────────────────────────────────────┐    │  │  │
│  │  │   │     Multi-Agent Graph                    │    │  │  │
│  │  │   │                                          │    │  │  │
│  │  │   │  ┌─────────┐                            │    │  │  │
│  │  │   │  │ Router  │  Intent Classification     │    │  │  │
│  │  │   │  │  Agent  │                            │    │  │  │
│  │  │   │  └────┬────┘                            │    │  │  │
│  │  │   │       │                                 │    │  │  │
│  │  │   │       ├──► RAG_QUERY ───┐               │    │  │  │
│  │  │   │       │                 │               │    │  │  │
│  │  │   │       └──► UTILITY ─────┼───┐           │    │  │  │
│  │  │   │                         │   │           │    │  │  │
│  │  │   │  ┌──────────────┐       │   │           │    │  │  │
│  │  │   │  │  Retriever   │◄──────┘   │           │    │  │  │
│  │  │   │  │    Agent     │            │           │    │  │  │
│  │  │   │  │  - Vector    │            │           │    │  │  │
│  │  │   │  │  - BM25      │            │           │    │  │  │
│  │  │   │  │  - Rerank    │            │           │    │  │  │
│  │  │   │  └──────┬───────┘            │           │    │  │  │
│  │  │   │         │                    │           │    │  │  │
│  │  │   │  ┌──────▼────────┐           │           │    │  │  │
│  │  │   │  │  Reasoning    │           │           │    │  │  │
│  │  │   │  │    Agent      │           │           │    │  │  │
│  │  │   │  │  - Chain of   │           │           │    │  │  │
│  │  │   │  │    Thought    │           │           │    │  │  │
│  │  │   │  │  - Citations  │           │           │    │  │  │
│  │  │   │  └───────────────┘           │           │    │  │  │
│  │  │   │                              │           │    │  │  │
│  │  │   │  ┌───────────────┐           │           │    │  │  │
│  │  │   │  │   Utility     │◄──────────┘           │    │  │  │
│  │  │   │  │    Agent      │                       │    │  │  │
│  │  │   │  │ - Summarize   │                       │    │  │  │
│  │  │   │  │ - Translate   │                       │    │  │  │
│  │  │   │  │ - Checklist   │                       │    │  │  │
│  │  │   │  └───────────────┘                       │    │  │  │
│  │  │   └──────────────────────────────────────────┘    │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────┬──────────────────────────────┘  │
└────────────────────────────────┼──────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼─────┐         ┌────▼─────┐         ┌─────▼────┐
    │ Google   │         │ Google   │         │  Google  │
    │ Gemini   │         │Embedding │         │  Vision  │
    │   API    │         │   API    │         │   API    │
    └──────────┘         └──────────┘         └──────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         PostgreSQL 16 with pgvector (Port 5432)            │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │ │
│  │  │  documents_  │  │  documents_    │  │  chat_         │  │ │
│  │  │  document    │  │  documentchunk │  │  chatsession   │  │ │
│  │  │              │  │                │  │                │  │ │
│  │  │ - id         │  │ - id           │  │ - id           │  │ │
│  │  │ - title      │  │ - document_id  │  │ - title        │  │ │
│  │  │ - file_path  │  │ - index        │  │ - created_at   │  │ │
│  │  │ - status     │  │ - text         │  │                │  │ │
│  │  │ - ...        │  │ - embedding    │  │                │  │ │
│  │  │              │  │   (vector[768])│  │                │  │ │
│  │  └──────────────┘  └───────────────┘  └────────────────┘  │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │ │
│  │  │  chat_       │  │  evaluation_  │  │  evaluation_   │  │ │
│  │  │  chatmessage │  │  testquery    │  │  evaluationrun │  │ │
│  │  │              │  │               │  │                │  │ │
│  │  │ - session_id │  │ - query       │  │ - run_name     │  │ │
│  │  │ - role       │  │ - expected    │  │ - avg_score    │  │ │
│  │  │ - content    │  │ - keywords    │  │ - results      │  │ │
│  │  │ - metadata   │  │               │  │                │  │ │
│  │  └──────────────┘  └───────────────┘  └────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Document Upload and Processing Flow

```
1. User uploads document via frontend
   ↓
2. POST /api/documents/upload/ (multipart/form-data)
   ↓
3. Django creates Document record (status: UPLOADED)
   ↓
4. DocumentProcessor service:
   a. Extract text (based on file type)
   b. Split into chunks (800 tokens, 200 overlap)
   c. Generate embeddings for each chunk (Gemini API)
   d. Store chunks with embeddings in DocumentChunk table
   ↓
5. Update Document status to READY
   ↓
6. Frontend polls and displays updated status
```

### Question Answering Flow

```
1. User types question in chat
   ↓
2. POST /api/chat/sessions/{id}/messages/
   ↓
3. Create ChatMessage (role: user)
   ↓
4. RAG Orchestrator processes query through LangGraph:
   
   a. Router Agent:
      - Analyzes query
      - Determines intent (RAG_QUERY, SUMMARIZE, TRANSLATE, CHECKLIST)
   
   b. If RAG_QUERY:
      - Retriever Agent:
        * Generate query embedding
        * Vector similarity search (cosine similarity)
        * BM25 keyword search
        * Combine and rerank results
        * Return top-K chunks
      
      - Reasoning Agent:
        * Receive retrieved chunks
        * Generate chain-of-thought prompt
        * Call Gemini API
        * Extract citations
        * Return answer
   
   c. If UTILITY (SUMMARIZE/TRANSLATE/CHECKLIST):
      - Utility Agent:
        * Construct task-specific prompt
        * Call Gemini API
        * Return processed result
   ↓
5. Create ChatMessage (role: assistant) with:
   - Answer
   - Citations (document_id, title, page, snippet)
   - Metadata
   ↓
6. Return response to frontend
   ↓
7. Frontend displays answer with citations
```

## Key Design Decisions

### 1. Multi-Agent Architecture (LangGraph)

**Why**: Modular, scalable, and maintainable. Each agent has a single responsibility.

- **Router Agent**: Handles intent classification
- **Retriever Agent**: Focuses on finding relevant information
- **Reasoning Agent**: Generates answers with citations
- **Utility Agent**: Handles auxiliary tasks

### 2. Hybrid Retrieval (BM25 + Vector)

**Why**: Combines semantic understanding (vectors) with keyword matching (BM25) for better recall.

**Implementation**:
- Vector search: Cosine similarity on Gemini embeddings
- BM25: Traditional keyword-based ranking
- Combined scoring: α * vector_score + (1-α) * bm25_score
- Reranking for diversity

### 3. PostgreSQL with pgvector

**Why**: 
- Single database for all data
- Native vector operations (efficient similarity search)
- ACID compliance
- Familiar SQL interface

### 4. Chunking Strategy

**Configuration**:
- Chunk size: 800 tokens (configurable)
- Overlap: 200 tokens (configurable)
- Splitter: Recursive character text splitter

**Why**:
- Balance between context and granularity
- Overlap ensures no information loss at boundaries
- Configurable for different use cases

### 5. Citation System

**Implementation**:
- Each answer includes source chunks
- Metadata: document ID, title, page number, snippet
- Enables fact-checking and transparency

## Scalability Considerations

### Current Architecture (Single Server)

Suitable for:
- Small to medium workloads (< 1000 documents)
- Single-tenant applications
- Development and testing

### Future Enhancements

1. **Async Task Processing**:
   - Add Celery + Redis
   - Background document processing
   - Queue management for high-volume uploads

2. **Caching**:
   - Redis for session and query caching
   - Reduce database load
   - Faster response times

3. **Load Balancing**:
   - Multiple backend instances
   - Nginx for load distribution
   - Database replication for read scaling

4. **Vector Database Migration**:
   - Consider Qdrant, Weaviate, or Pinecone
   - Better performance at scale (> 100K documents)
   - Advanced vector search features

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **File Upload**: Validate file types and sizes
3. **Input Sanitization**: Prevent SQL injection, XSS
4. **CORS**: Configure allowed origins properly in production
5. **Rate Limiting**: Add rate limiting for API endpoints
6. **Authentication**: Add user authentication (currently not implemented)

## Monitoring and Logging

**Recommended**:
- Application logging (Django logging framework)
- Error tracking (Sentry)
- Performance monitoring (New Relic, Datadog)
- Database query monitoring
- API response time tracking

## Testing Strategy

1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: API endpoints
3. **End-to-End Tests**: Full workflows
4. **Performance Tests**: Load testing for scalability
5. **Evaluation Tests**: QA accuracy metrics

Target: 100% test coverage on business logic
