# Intelligent Document Question Answering System

A multi-agent document-based Question Answering system built with **Hexagonal Architecture**, Django, React, LangChain, LangGraph, and Google Gemini AI. Now using **UV package manager** for fast and reliable dependency management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Development](#development)
- [Project Structure](#project-structure)

## 🔍 Overview

This system enables users to upload documents (PDF, DOCX, TXT, images) and ask natural language questions. The system uses a multi-agent architecture with LangGraph to orchestrate retrieval, reasoning, and utility functions (translation, summarization, checklist generation) in both English and Persian.

## ✨ Features

- **Document Upload & Processing**
  - Support for PDF, DOCX, TXT, JPG, PNG formats
  - Automatic text extraction (OCR for images)
  - Document chunking with overlap
  - Vector embeddings using Google Gemini

- **Multi-Agent Orchestration (LangGraph)**
  - **Router Agent**: Classifies user intent
  - **Retriever Agent**: Hybrid search (BM25 + vector similarity)
  - **Reasoning Agent**: Chain-of-thought answering with citations
  - **Utility Agent**: Translation (EN↔FA), summarization, checklist generation

- **Question Answering**
  - Natural language queries
  - Grounded answers with document citations
  - Conversation context awareness
  - Fallback handling for unclear queries

- **Evaluation System**
  - Automated testing with predefined queries
  - Performance metrics and scoring
  - Evaluation history tracking

- **Multilingual Support**
  - Full English and Persian support
  - Natural language utility commands

## 🏗 Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters) for clean separation of concerns. See [HEXAGONAL_ARCHITECTURE.md](HEXAGONAL_ARCHITECTURE.md) for detailed documentation.

### High-Level Overview

```
┌─────────────┐
│   Frontend  │ (React SPA)
│  (Port 3000)│
└──────┬──────┘
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────┐
│      Backend (Django + Hexagonal Arch)      │
│              (Port 8000)                     │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │   API Layer (HTTP Adapters)            │ │
│  └────────────┬───────────────────────────┘ │
│               │                              │
│  ┌────────────▼───────────────────────────┐ │
│  │   Application Layer (Use Cases)        │ │
│  └────────────┬───────────────────────────┘ │
│               │                              │
│  ┌────────────▼───────────────────────────┐ │
│  │   Domain Layer (Business Logic)        │ │
│  └────────────┬───────────────────────────┘ │
│               │                              │
│  ┌────────────▼───────────────────────────┐ │
│  │   Infrastructure Layer (Adapters)      │ │
│  │   - Django ORM Repositories            │ │
│  │   - Gemini AI Services                 │ │
│  │   RAG Orchestration (LangGraph)        │ │
│  │                                        │ │
│  │  ┌──────────┐  ┌───────────┐         │ │
│  │  │  Router  │─►│ Retriever │         │ │
│  │  └──────────┘  └─────┬─────┘         │ │
│  │       │              │                │ │
│  │       │         ┌────▼──────┐        │ │
│  │       │         │ Reasoner  │        │ │
│  │       │         └───────────┘        │ │
│  │       │                              │ │
│  │       │         ┌──────────┐        │ │
│  │       └────────►│ Utility  │        │ │
│  │                 └──────────┘        │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │   Document Processing Service     │  │
│  │   - Text Extraction               │  │
│  │   - Chunking                      │  │
│  │   - Embedding Generation          │  │
│  └───────────────────────────────────┘  │
│                                          │
└──────────────┬───────────────────────────┘
               │
    ┌──────────▼──────────┐
    │   PostgreSQL +      │
    │     pgvector        │
    │    (Port 5432)      │
    └─────────────────────┘
```

### Agent Flow

```
User Query
    │
    ▼
┌─────────┐
│ Router  │ → Classify Intent (RAG_QUERY / SUMMARIZE / TRANSLATE / CHECKLIST)
└────┬────┘
     │
     ├─ RAG_QUERY ──► Retriever ──► Reasoner ──► Answer + Citations
     │
     └─ UTILITY ────► Utility Agent ──► Processed Result
```

## 🛠 Tech Stack

### Backend
- **Architecture**: Hexagonal Architecture (Ports & Adapters)
- **Framework**: Django 5.0 + Django REST Framework
- **Package Manager**: UV (fast Python package installer)
- **AI/ML**: LangChain, LangGraph, Google Gemini APIs
- **Database**: PostgreSQL with pgvector extension
- **Document Processing**: PyPDF2, pdfplumber, python-docx, Google Vision API
- **Search**: BM25 (rank-bm25) + Vector Similarity

### Frontend
- **Framework**: React 18
- **State Management**: React Query
- **HTTP Client**: Axios
- **Styling**: CSS3 with responsive design

### DevOps
- **Containerization**: Docker + Docker Compose
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, isort, flake8, pre-commit

## 📦 Installation

### Prerequisites

- Docker & Docker Compose (or UV + Python 3.11+)
- Google API Key (for Gemini)
- Git

> **Note**: The project now uses **UV** package manager for faster dependency management.

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intelligent-doc-qa
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```
   
   Edit `backend/.env` and add your Google API key:
   ```env
   GOOGLE_API_KEY=your-google-api-key-here
   ```

3. **Build and start services**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin

5. **Create Django superuser** (optional)
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## 🚀 Usage

### Uploading Documents

1. Open the frontend at http://localhost:3000
2. Click on the upload area or drag-and-drop files
3. Supported formats: PDF, DOCX, TXT, JPG, PNG
4. Wait for processing (status will update automatically)

### Asking Questions

1. Once documents are processed (status: READY)
2. Type your question in the chat input
3. Press Send or hit Enter
4. View the answer with document citations

### Using Utility Functions

All utility functions are triggered via natural language:

**Summarization**:
```
"Summarize this document"
"خلاصه این متن را بده"
```

**Translation**:
```
"Translate this to Persian"
"به انگلیسی ترجمه کن"
```

**Checklist**:
```
"Create a checklist from this content"
"از این سند چک‌لیست بساز"
```

## 📚 API Documentation

### Documents API

**Upload Document**
```http
POST /api/documents/upload/
Content-Type: multipart/form-data

{
  "file": <binary>,
  "title": "Optional Title",
  "language": "en"
}
```

**List Documents**
```http
GET /api/documents/
```

**Get Document Details**
```http
GET /api/documents/{id}/
```

### Chat API

**Create Session**
```http
POST /api/chat/sessions/
{
  "title": "My Chat Session"
}
```

**Send Message**
```http
POST /api/chat/sessions/{id}/messages/
{
  "content": "What is the main topic of the document?"
}
```

**Response Format**:
```json
{
  "answer": "The main topic is...",
  "citations": [
    {
      "document_id": 1,
      "document_title": "Report.pdf",
      "chunk_index": 5,
      "page": 3,
      "snippet": "..."
    }
  ],
  "session_id": 1,
  "message_id": 10,
  "metadata": {...}
}
```

### Evaluation API

**Run Evaluation**
```http
POST /api/evaluation/runs/run/
{
  "run_name": "Test Run 1",
  "test_query_ids": [1, 2, 3]
}
```

**Get Evaluation Results**
```http
GET /api/evaluation/runs/
```

## 🧪 Testing

### Running Tests

**All tests with coverage**:
```bash
docker-compose exec backend pytest
```

**Specific app tests**:
```bash
docker-compose exec backend pytest documents/
docker-compose exec backend pytest chat/
docker-compose exec backend pytest evaluation/
docker-compose exec backend pytest rag/
```

**Coverage report**:
```bash
docker-compose exec backend pytest --cov-report=html
```

View HTML coverage report: `backend/htmlcov/index.html`

### Pre-commit Hooks

**Install pre-commit hooks**:
```bash
pip install pre-commit
pre-commit install
```

**Run manually**:
```bash
pre-commit run --all-files
```

## 💻 Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run development server
python manage.py runserver 0.0.0.0:8000
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend sh

# Install dependencies
npm install

# Start development server
npm start
```

### Code Quality

The project enforces code quality through:
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pre-commit**: Automated checks

## 📁 Project Structure (Hexagonal Architecture)

```
intelligent-doc-qa/
├── backend/
│   ├── core/                # Core business logic (hexagonal)
│   │   ├── domain/          # Domain entities & value objects
│   │   │   ├── entities/    # Document, Chunk, Chat entities
│   │   │   ├── value_objects/  # Status, FileType, Embedding
│   │   │   ├── services/    # Domain services
│   │   │   └── exceptions.py
│   │   ├── application/     # Use cases & ports
│   │   │   ├── use_cases/   # UploadDocument, ProcessDocument, AskQuestion
│   │   │   ├── dto/         # Data Transfer Objects
│   │   │   └── ports/       # Interfaces (repositories, services)
│   │   └── infrastructure/  # Adapters
│   │       ├── adapters/    # Repository & service implementations
│   │       │   ├── repositories/  # Django ORM adapters
│   │       │   ├── services/      # Gemini, text extractors
│   │       │   └── rag/           # LangGraph orchestrator
│   │       └── persistence/ # Django models
│   ├── api/                 # HTTP adapters
│   │   └── v1/              # API v1 endpoints
│   ├── config/              # Django settings
│   ├── documents/           # Legacy app (kept for migrations)
│   ├── chat/                # Legacy app (kept for migrations)
│   ├── evaluation/          # Evaluation app
│   ├── rag/                 # Legacy RAG (wrapped by adapter)
│   ├── manage.py
│   ├── pyproject.toml       # UV dependencies
│   ├── uv.lock              # Locked dependencies
│   ├── Dockerfile           # Updated for UV
│   └── pytest.ini
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `backend/.env.example`):

- `GOOGLE_API_KEY`: Google Gemini API key (required)
- `CHUNK_SIZE`: Text chunk size (default: 800)
- `CHUNK_OVERLAP`: Chunk overlap size (default: 200)
- `TOP_K_RETRIEVAL`: Number of chunks to retrieve (default: 5)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.7)

### Chunking Parameters

Adjust in `backend/.env`:
```env
CHUNK_SIZE=800
CHUNK_OVERLAP=200
```

### Retrieval Parameters

```env
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and pre-commit hooks
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with LangChain and LangGraph
- Powered by Google Gemini AI
- PostgreSQL with pgvector extension

---

For questions or issues, please open a GitHub issue.
