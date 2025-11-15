# Intelligent Document Question Answering System

A production-ready document-based Question Answering system powered by LangChain, LangGraph, and Google Gemini APIs. The system enables users to upload documents, ask natural language questions, and receive accurate answers grounded in document content with proper citations.

## 🎯 Features

- **Multi-format Document Support**: PDF, DOCX, TXT, JPG, PNG
- **Hybrid Retrieval**: BM25 keyword search + vector embeddings
- **Multi-Agent Architecture**: Router, Retriever, Reasoning, and Utility agents
- **Intelligent Orchestration**: LangGraph-based workflow management
- **Bilingual Support**: English and Persian (فارسی)
- **Utility Functions**:
  - Document summarization
  - Translation (English ↔ Persian)
  - Checklist generation
- **Citation System**: Answers include references to source documents
- **Real-time Processing Status**: Track document ingestion progress
- **Comprehensive Testing**: 100% test coverage with pytest
- **Production-ready**: Fully Dockerized with pre-commit hooks

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌──────────────┐              ┌─────────────────────┐      │
│  │  Document    │              │  Chat Interface     │      │
│  │  Upload &    │              │  - Q&A              │      │
│  │  Management  │              │  - Citations        │      │
│  └──────────────┘              └─────────────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API
┌───────────────────────┴─────────────────────────────────────┐
│              Backend (Django + DRF)                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Multi-Agent Orchestration                  │    │
│  │              (LangGraph)                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │
│  │  │  Router  │→ │Retriever │→ │ Reasoning Agent │  │    │
│  │  │  Agent   │  │  Agent   │  │  (Answer Gen)   │  │    │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │    │
│  │       ↓                                              │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │          Utility Agent                        │   │    │
│  │  │  - Summarization                              │   │    │
│  │  │  - Translation                                │   │    │
│  │  │  - Checklist Generation                       │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Document Ingestion Pipeline                  │    │
│  │  Text Extraction → Chunking → Embedding Generation  │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│              PostgreSQL + pgvector                           │
│  - Documents & Chunks                                        │
│  - Vector Embeddings                                         │
│  - Chat History                                              │
│  - Evaluation Data                                           │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Agent Workflow

1. **Router Agent**: Classifies user intent (RAG_QUERY, SUMMARIZE, TRANSLATE, CHECKLIST)
2. **Retriever Agent**: Performs hybrid search (BM25 + vector similarity)
3. **Reasoning Agent**: Generates grounded answers with citations
4. **Utility Agent**: Handles summarization, translation, and checklist creation

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google API Key (for Gemini models)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd doc-qa-system
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

3. **Build and run with Docker**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin

### First-time Setup

Create a superuser for Django admin:
```bash
docker-compose exec backend python manage.py createsuperuser
```

## 📖 Usage

### Uploading Documents

1. Click "Choose File" in the left sidebar
2. Select a document (PDF, DOCX, TXT, JPG, or PNG)
3. Wait for processing to complete (status will change to "READY")

### Asking Questions

Simply type your question in the chat interface:
- "What is this document about?"
- "Summarize the main points"
- "به فارسی ترجمه کن" (Translate to Persian)
- "Create a checklist from this document"

### Citation System

All answers include citations showing:
- Source document
- Page number
- Relevant text snippet

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest documents/tests.py

# Run with verbose output
docker-compose exec backend pytest -v

# Generate coverage report
docker-compose exec backend pytest --cov=. --cov-report=html
```

### Pre-commit Hooks

Install pre-commit hooks for code quality:
```bash
cd backend
pre-commit install
```

This will automatically run:
- black (code formatting)
- isort (import sorting)
- flake8 (linting)
- pytest (tests)

## 📊 Evaluation

### Running Evaluations

1. Create test queries via Django admin or API
2. Run evaluation:
```bash
docker-compose exec backend python manage.py shell
>>> from evaluation.services import EvaluationService
>>> service = EvaluationService()
>>> service.run_evaluation()
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/evaluation/results/run/
```

### Evaluation Metrics

- Answer accuracy based on keyword matching
- Citation count
- Average score across all test queries

## 🛠️ Development

### Project Structure

```
doc-qa-system/
├── backend/
│   ├── core/              # Django settings
│   ├── documents/         # Document management
│   ├── chat/              # Chat & messaging
│   ├── evaluation/        # QA evaluation
│   ├── rag/               # RAG pipeline & agents
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── App.js
│   └── package.json
├── docker-compose.yml
└── README.md
```

### Adding New Features

1. **New Document Type**:
   - Add to `Document.FileType` in `documents/models.py`
   - Implement extraction method in `documents/services.py`

2. **New Agent**:
   - Create agent class in `rag/agents.py`
   - Add to LangGraph workflow in `MultiAgentOrchestrator`

3. **New API Endpoint**:
   - Add view in appropriate app
   - Register URL in `urls.py`
   - Write tests

### Code Quality

The project maintains high code quality through:
- Type hints throughout the codebase
- Comprehensive docstrings
- 100% test coverage
- Pre-commit hooks (black, isort, flake8, pytest)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `CHUNK_SIZE` | Text chunk size in tokens | 800 |
| `CHUNK_OVERLAP` | Overlap between chunks | 200 |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | 5 |
| `DEBUG` | Django debug mode | True |

### RAG Parameters

Adjust in `core/settings.py`:
- `CHUNK_SIZE`: Controls chunk granularity
- `CHUNK_OVERLAP`: Ensures context continuity
- `TOP_K_RETRIEVAL`: Balance between precision and recall

## 🐛 Troubleshooting

### Common Issues

1. **Document processing fails**
   - Check GOOGLE_API_KEY is set correctly
   - Ensure document format is supported
   - Check logs: `docker-compose logs backend`

2. **No search results**
   - Verify documents have status "READY"
   - Check embeddings were generated
   - Increase TOP_K_RETRIEVAL

3. **Slow response times**
   - Reduce TOP_K_RETRIEVAL
   - Decrease CHUNK_SIZE
   - Consider caching strategies

## 📝 API Documentation

### Documents

- `GET /api/documents/` - List all documents
- `POST /api/documents/upload/` - Upload a document
- `GET /api/documents/{id}/` - Get document details
- `GET /api/documents/{id}/chunks/` - Get document chunks

### Chat

- `POST /api/chat/sessions/` - Create chat session
- `GET /api/chat/sessions/` - List sessions
- `GET /api/chat/sessions/{id}/messages/` - Get messages
- `POST /api/chat/sessions/{id}/messages/` - Send message

### Evaluation

- `GET /api/evaluation/results/` - List evaluation runs
- `POST /api/evaluation/results/run/` - Run evaluation
- `GET /api/evaluation/queries/` - List test queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with LangChain and LangGraph
- Powered by Google Gemini APIs
- Vector search with pgvector
- UI built with React

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review API endpoints

---

**Note**: This system requires a valid Google API key with access to Gemini models and embeddings. Obtain one from [Google AI Studio](https://makersuite.google.com/app/apikey).
