# System Architecture

## Overview

The Intelligent Document Q&A System is built using a microservices architecture with three main components:

1. **Frontend** (React SPA)
2. **Backend** (Django REST API)
3. **Database** (PostgreSQL with pgvector)

## Component Architecture

### 1. Frontend Layer

**Technology**: React 18+ with modern hooks

**Components**:
- `DocumentList`: Handles file uploads and displays document status
- `ChatInterface`: Provides conversational UI for Q&A
- `API Service`: Centralized API communication with axios

**Features**:
- Real-time status polling for document processing
- Bilingual support (English/Persian)
- Citation display with document references
- Responsive design

### 2. Backend Layer

**Technology**: Django 5.0 + Django REST Framework

**Applications**:

#### a) Documents App
- **Models**: `Document`, `DocumentChunk`
- **Services**: `DocumentIngestionService`
- **Responsibilities**:
  - File upload handling
  - Text extraction (PDF, DOCX, TXT, images)
  - Document chunking with overlap
  - Embedding generation via Gemini
  - Status management

#### b) RAG Module
- **Components**: `RetrievalService`, Multi-agent system
- **Responsibilities**:
  - Hybrid retrieval (BM25 + vector search)
  - Query embedding generation
  - Result combination and reranking

#### c) Chat App
- **Models**: `ChatSession`, `ChatMessage`
- **Responsibilities**:
  - Session management
  - Message persistence
  - Conversation history tracking

#### d) Evaluation App
- **Models**: `TestQuery`, `EvaluationRun`, `QueryEvaluation`
- **Responsibilities**:
  - Test query management
  - Automated evaluation
  - Metrics calculation

### 3. Multi-Agent System (LangGraph)

**Architecture**: State-based workflow with conditional routing

**Agents**:

1. **Router Agent**
   - Classifies user intent
   - Routes to appropriate handler
   - Intents: RAG_QUERY, SUMMARIZE, TRANSLATE, CHECKLIST

2. **Retriever Agent**
   - Executes hybrid search
   - Combines BM25 and vector results
   - Returns top-K chunks with metadata

3. **Reasoning Agent**
   - Chain-of-thought reasoning
   - Grounded answer generation
   - Citation extraction

4. **Utility Agent**
   - Summarization
   - Translation (English ↔ Persian)
   - Checklist generation

**Workflow**:
```
User Query
    ↓
Router Agent (intent classification)
    ↓
   / \
  /   \
RAG    Utility
 ↓       ↓
Retriever  (direct to Utility Agent)
 ↓
Reasoning Agent
 ↓
Response + Citations
```

### 4. Data Layer

**PostgreSQL with pgvector Extension**

**Schema Design**:

```sql
-- Documents
Document
  - id (PK)
  - title
  - file
  - file_type
  - status (UPLOADED, PROCESSING, READY, FAILED)
  - error_message
  - timestamps

-- Chunks with embeddings
DocumentChunk
  - id (PK)
  - document_id (FK)
  - index
  - text
  - page_number
  - embedding (vector(768))
  - created_at

-- Chat sessions
ChatSession
  - id (PK)
  - title
  - timestamps

-- Messages
ChatMessage
  - id (PK)
  - session_id (FK)
  - role (user/assistant/system)
  - content
  - metadata (JSON: citations, intent)
  - created_at

-- Evaluation
TestQuery
  - id (PK)
  - query
  - expected_keywords (JSON array)
  - language
  - category
  - is_active

EvaluationRun
  - id (PK)
  - started_at
  - completed_at
  - total_queries
  - average_score
  - results (JSON)

QueryEvaluation
  - id (PK)
  - run_id (FK)
  - test_query_id (FK)
  - answer
  - score
  - citations_count
  - metadata (JSON)
```

## Data Flow

### Document Ingestion Flow

```
1. User uploads file
   ↓
2. Document record created (status: UPLOADED)
   ↓
3. DocumentIngestionService.process_document()
   ↓
4. Status → PROCESSING
   ↓
5. Extract text based on file type
   - PDF: pdfplumber
   - DOCX: python-docx
   - TXT: direct read
   - Images: Gemini Vision OCR
   ↓
6. Create overlapping chunks
   ↓
7. Generate embeddings (Gemini embedding-001)
   ↓
8. Store chunks with embeddings in DB
   ↓
9. Status → READY (or FAILED on error)
```

### Query Processing Flow

```
1. User sends message
   ↓
2. Create ChatMessage (role: user)
   ↓
3. Build conversation context
   ↓
4. Initialize LangGraph workflow
   ↓
5. Router Agent classifies intent
   ↓
6a. RAG Path:
    - Retriever Agent: hybrid search
    - Reasoning Agent: generate answer + citations
   ↓
6b. Utility Path:
    - Utility Agent: summarize/translate/checklist
   ↓
7. Create ChatMessage (role: assistant)
   ↓
8. Return response to frontend
```

## Technology Stack

### Backend
- **Framework**: Django 5.0
- **API**: Django REST Framework
- **Database**: PostgreSQL 16 with pgvector
- **Vector Search**: pgvector
- **LLM Framework**: LangChain + LangGraph
- **LLM Provider**: Google Gemini (gemini-pro, embedding-001)
- **OCR**: Google Vision API / Gemini Vision
- **Text Processing**: pdfplumber, python-docx
- **Keyword Search**: rank-bm25
- **Testing**: pytest, pytest-django, pytest-cov
- **Code Quality**: black, isort, flake8, pre-commit

### Frontend
- **Framework**: React 18
- **HTTP Client**: axios
- **State Management**: React hooks
- **Styling**: CSS3 with modern features
- **Build Tool**: Create React App

### DevOps
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (frontend)
- **App Server**: Gunicorn (backend)
- **Database**: PostgreSQL with pgvector extension

## Design Decisions

### 1. Hybrid Retrieval
**Decision**: Combine BM25 and vector search

**Rationale**:
- BM25 captures exact keyword matches
- Vector search captures semantic similarity
- Combination improves recall and precision

### 2. Overlapping Chunks
**Decision**: 800-token chunks with 200-token overlap

**Rationale**:
- Preserves context across chunk boundaries
- Balances granularity and context
- Prevents information loss

### 3. LangGraph for Orchestration
**Decision**: Use LangGraph instead of simple chains

**Rationale**:
- Conditional routing based on intent
- State management across agents
- Extensibility for new agents
- Clear workflow visualization

### 4. pgvector for Embeddings
**Decision**: Store embeddings in PostgreSQL with pgvector

**Rationale**:
- No separate vector database needed
- ACID compliance
- Simplified architecture
- Efficient similarity search

### 5. Citation System
**Decision**: Include document references with every answer

**Rationale**:
- Builds user trust
- Enables verification
- Transparent AI reasoning
- Meets academic/professional standards

## Performance Considerations

### Scalability
- **Database**: Indexed vector searches
- **API**: Stateless design for horizontal scaling
- **Caching**: Consider Redis for frequent queries
- **Background Processing**: Use Celery for async document processing

### Optimization Opportunities
1. **Embedding Cache**: Cache query embeddings
2. **Chunk Pruning**: Pre-filter chunks before vector search
3. **Batch Processing**: Process multiple documents concurrently
4. **Query Expansion**: Enhance retrieval with synonyms
5. **Re-ranking**: Advanced re-ranking algorithms

## Security Considerations

1. **API Authentication**: Add JWT/OAuth for production
2. **File Validation**: Strict file type and size limits
3. **Input Sanitization**: Prevent injection attacks
4. **Rate Limiting**: Protect against abuse
5. **CORS**: Configured for specific origins
6. **Environment Variables**: Secrets management

## Testing Strategy

### Unit Tests
- Individual model methods
- Service functions
- Agent behaviors
- API serializers

### Integration Tests
- API endpoints
- Multi-agent workflows
- Database operations
- File processing

### End-to-End Tests
- Complete user flows
- Document upload → Q&A
- Evaluation pipeline

### Coverage Target
- **Goal**: 100% coverage
- **Focus**: Core business logic
- **Tools**: pytest-cov

## Deployment

### Docker Compose (Development)
```bash
docker-compose up --build
```

### Production Considerations
1. Use production-grade secret management
2. Set DEBUG=False
3. Configure proper ALLOWED_HOSTS
4. Use managed database (RDS, Cloud SQL)
5. Set up monitoring (Sentry, Datadog)
6. Configure logging
7. Enable HTTPS
8. Set up CI/CD pipeline

## Future Enhancements

1. **Multi-user Support**: User authentication and document isolation
2. **Advanced RAG**: Query expansion, hypothetical document embeddings
3. **Streaming Responses**: Real-time answer generation
4. **Document Comparison**: Multi-document Q&A
5. **Voice Interface**: Speech-to-text and text-to-speech
6. **Analytics Dashboard**: Usage metrics and insights
7. **Custom Models**: Fine-tuned embeddings and LLMs
8. **Collaborative Features**: Shared sessions and annotations
