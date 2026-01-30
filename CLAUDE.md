# CLAUDE.md

## Project Overview

Intelligent Document Question Answering System — a full-stack AI application that lets users upload documents (PDF, DOCX, TXT, images) and ask natural language questions. Uses a multi-agent LangGraph architecture for retrieval, reasoning, and utility tasks. Supports English and Persian.

## Tech Stack

- **Backend**: Django 5.0 + Django REST Framework, Python 3.11, UV package manager
- **Frontend**: React 18, React Query, Axios
- **Database**: PostgreSQL 16 with pgvector extension (768-dim vectors)
- **AI/ML**: LangGraph (multi-agent), LangChain, Google Gemini (LLM: `gemini-2.5-flash`, embeddings: `text-embedding-004`), Google Vision API (OCR)
- **DevOps**: Docker Compose, pre-commit hooks (black, isort, flake8)

## Repository Structure

```
backend/
  core/
    domain/          # Pure domain entities, value objects, exceptions (no framework deps)
    application/     # Use cases, DTOs, ports (interfaces)
    infrastructure/  # Adapters: Django ORM repos, Gemini services, LangGraph RAG
  api/v1/            # REST API endpoints (ViewSets)
  documents/         # Document management Django app + migrations
  chat/              # Chat session Django app + migrations
  evaluation/        # Evaluation system Django app + migrations
  rag/               # RAG orchestration module
  config/            # Django settings
  tests/             # pytest test suite
  pyproject.toml     # Python dependencies (UV)
  Dockerfile
frontend/
  src/
    components/      # DocumentList, ChatInterface
    services/        # Axios API client
  Dockerfile
docker-compose.yml   # PostgreSQL + Backend + Frontend
init-db.sql          # pgvector extension init
notebooks/           # Jupyter exploration notebooks (01-03)
```

## Architecture

**Hexagonal Architecture (Ports & Adapters):**

1. **Domain** (`core/domain/`) — Pure entities (`Document`, `DocumentChunk`, `ChatSession`, `ChatMessage`), value objects (`DocumentStatus`, `FileType`, `Embedding`), custom exceptions. Zero framework imports.
2. **Application** (`core/application/`) — Use cases (`UploadDocumentUseCase`, `ProcessDocumentUseCase`, `AskQuestionUseCase`), DTOs, port interfaces.
3. **Infrastructure** (`core/infrastructure/`) — Django ORM repositories, Gemini service adapters, LangGraph RAG orchestrator.
4. **API** (`api/v1/`) — DRF ViewSets, serializers.

**Dependency Injection**: Central `DependencyContainer` singleton in `core/dependencies.py` with convenience functions like `get_upload_document_use_case()`.

**Multi-Agent Flow (LangGraph):**
```
Query -> Router Agent -> RAG_QUERY  -> Retriever -> Reasoner -> Answer + Citations
                      -> UTILITY    -> Utility Agent (summarize/translate/checklist)
```

**Hybrid Retrieval**: alpha=0.7 vector similarity + 0.3 BM25 keyword search, with diversity reranking.

## Build & Run

```bash
# Full stack (Docker)
docker-compose up --build

# Access points
# Frontend:  http://localhost:3000
# Backend:   http://localhost:9000
# Admin:     http://localhost:9000/admin
```

**Startup order**: PostgreSQL (with health check) -> Backend (migrations + runserver) -> Frontend.

**Backend commands inside container:**
```bash
docker-compose exec backend uv run python manage.py migrate
docker-compose exec backend uv run python manage.py makemigrations
docker-compose exec backend uv run python manage.py runserver 0.0.0.0:8000
```

## Testing

```bash
docker-compose exec backend pytest                         # All tests
docker-compose exec backend pytest --cov                   # With coverage
docker-compose exec backend pytest tests/test_chat.py      # Specific file
docker-compose exec backend pytest -m unit                 # By marker
docker-compose exec backend pytest --cov-report=html       # HTML report
```

**Test markers**: `unit`, `integration`, `slow`

**Test files** in `backend/tests/`: `test_chat.py`, `test_documents.py`, `test_evaluation.py`, `test_domain.py`, `test_rag.py`, `conftest.py` (fixtures).

**Coverage targets**: `documents`, `chat`, `evaluation`, `rag`, `core`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/documents/upload/` | Upload document (multipart/form-data) |
| GET | `/api/documents/` | List documents |
| GET | `/api/documents/{id}/` | Document details with chunks |
| DELETE | `/api/documents/{id}/` | Delete document |
| POST | `/api/chat/sessions/` | Create chat session |
| GET | `/api/chat/sessions/` | List sessions |
| POST | `/api/chat/sessions/{id}/messages/` | Send message, get AI answer |
| GET | `/api/chat/sessions/{id}/messages/` | Get session messages |
| DELETE | `/api/chat/sessions/{id}/clear/` | Clear session messages |
| POST | `/api/evaluation/runs/run/` | Run evaluation |
| GET | `/api/evaluation/runs/` | List evaluation runs |
| GET | `/api/evaluation/runs/{id}/` | Evaluation run details |

## Code Conventions

- **Python style**: black (line-length 100), isort (black profile), flake8 (line-length 100)
- **Naming**: snake_case for functions/variables, PascalCase for classes, `Django` prefix for ORM adapters, `Service` suffix for service implementations
- **Architecture rule**: Domain layer must have zero framework imports. All external dependencies flow through ports (interfaces) in the application layer.
- **Serializers**: Multiple serializers per ViewSet action when needed
- **Pre-commit hooks**: black, isort, flake8, trailing whitespace, JSON/YAML validation, large file detection, merge conflict detection, private key detection, pytest on push

## Environment Variables

Key variables (set in `.env` or `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Google Gemini API key (required) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | LLM model |
| `GEMINI_EMBEDDING_MODEL` | `models/text-embedding-004` | Embedding model |
| `CHUNK_SIZE` | `800` | Document chunk size in tokens |
| `CHUNK_OVERLAP` | `200` | Chunk overlap in tokens |
| `TOP_K_RETRIEVAL` | `5` | Number of chunks retrieved |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score |
| `DB_HOST` | `db` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DEBUG` | `True` | Django debug mode |

## Database

- PostgreSQL 16 with `pgvector` extension (auto-initialized via `init-db.sql`)
- Vector dimensions: 768 (Gemini embeddings)
- Key models: `Document` (status: UPLOADED/PROCESSING/READY/FAILED), `DocumentChunk` (with embedding VectorField), `ChatSession`, `ChatMessage`, `TestQuery`, `EvaluationRun`, `QueryResult`
- Unique constraint on `(document, chunk_index)`

## Common Tasks for AI Assistants

- **Adding a new endpoint**: Create serializer in the relevant app, add ViewSet action in `api/v1/`, register in URL config.
- **Adding a new agent**: Define in `core/infrastructure/`, wire into LangGraph orchestrator in `rag/`, add routing case in Router Agent.
- **Modifying domain logic**: Edit `core/domain/` entities (keep framework-free), update DTOs in `core/application/` if needed.
- **Adding dependencies**: Edit `backend/pyproject.toml`, run `uv lock` inside container.
- **Database changes**: Modify Django models, run `makemigrations` then `migrate`.
- **Running pre-commit**: `pre-commit run --all-files` from the repo root.
