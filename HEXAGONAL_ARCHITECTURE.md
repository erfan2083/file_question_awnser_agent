# Hexagonal Architecture Documentation

## Overview

This project has been refactored to follow **Hexagonal Architecture** (also known as Ports and Adapters). This architectural pattern separates the core business logic from external concerns, making the codebase more maintainable, testable, and flexible.

## Architecture Layers

### 1. **Domain Layer** (`core/domain/`)

The innermost layer containing pure business logic with **zero dependencies** on frameworks or external libraries.

#### Entities (`core/domain/entities/`)
- **`document.py`**: Document entity with business rules for status transitions
- **`chunk.py`**: DocumentChunk entity for text chunks with embeddings
- **`chat.py`**: Chat entities (ChatSession, ChatMessage, Citation)

#### Value Objects (`core/domain/value_objects/`)
- **`document_status.py`**: Document status enum with validation
- **`file_type.py`**: File type enum with utility methods
- **`embedding.py`**: Embedding value object with similarity calculations

#### Domain Services (`core/domain/services/`)
- Domain services for complex business logic that doesn't fit in entities

#### Exceptions (`core/domain/exceptions.py`)
- Domain-specific exceptions

### 2. **Application Layer** (`core/application/`)

Orchestrates domain logic to implement use cases. This layer is framework-agnostic.

#### Use Cases (`core/application/use_cases/`)
- **`upload_document.py`**: Handle document uploads
- **`process_document.py`**: Process documents (extract, chunk, embed)
- **`ask_question.py`**: Answer questions using RAG

#### DTOs (`core/application/dto/`)
Data Transfer Objects for input/output across boundaries:
- **`document_dto.py`**: Document-related DTOs
- **`chat_dto.py`**: Chat-related DTOs

#### Ports (`core/application/ports/`)
Interfaces that define contracts for external dependencies:

**Repositories** (`ports/repositories/`):
- `DocumentRepository`: Interface for document persistence
- `ChunkRepository`: Interface for chunk persistence
- `ChatSessionRepository`: Interface for chat session persistence
- `ChatMessageRepository`: Interface for message persistence

**Services** (`ports/services/`):
- `TextExtractor`: Interface for text extraction
- `EmbeddingService`: Interface for embedding generation
- `LLMService`: Interface for LLM operations
- `RAGService`: Interface for RAG orchestration

### 3. **Infrastructure Layer** (`core/infrastructure/`)

Implements the ports with concrete adapters for external systems.

#### Adapters (`core/infrastructure/adapters/`)

**Repositories** (`adapters/repositories/`):
- `DjangoDocumentRepository`: Django ORM implementation
- `DjangoChunkRepository`: Django ORM implementation
- `DjangoChatRepository`: Django ORM implementation

**Services** (`adapters/services/`):
- `GeminiEmbeddingService`: Gemini API for embeddings
- `GeminiLLMService`: Gemini API for LLM
- `PDFTextExtractor`: PDF text extraction
- `DOCXTextExtractor`: DOCX text extraction
- `TXTTextExtractor`: TXT text extraction

**RAG** (`adapters/rag/`):
- `LangGraphRAGService`: LangGraph multi-agent orchestration

#### Persistence (`core/infrastructure/persistence/`)
- `models.py`: Django ORM models (moved from app-level)

### 4. **API Layer** (`api/`)

HTTP adapters that expose the application through REST APIs.

- **`api/v1/documents/`**: Document management endpoints
- **`api/v1/chat/`**: Chat endpoints
- **`api/v1/evaluation/`**: Evaluation endpoints

## Dependency Flow

```
┌─────────────────────────────────────────────────┐
│              API Layer (HTTP)                    │
│         (Views, Serializers, URLs)              │
└───────────────────┬─────────────────────────────┘
                    │ uses
                    ▼
┌─────────────────────────────────────────────────┐
│          Application Layer (Use Cases)          │
│     - UploadDocumentUseCase                     │
│     - ProcessDocumentUseCase                    │
│     - AskQuestionUseCase                        │
└───────────────────┬─────────────────────────────┘
                    │ orchestrates
                    ▼
┌─────────────────────────────────────────────────┐
│          Domain Layer (Business Logic)          │
│     - Entities (Document, Chunk, Chat)          │
│     - Value Objects (Status, FileType)          │
│     - Domain Services                           │
└─────────────────────────────────────────────────┘
                    ▲
                    │ implements
┌───────────────────┴─────────────────────────────┐
│     Infrastructure Layer (Adapters)             │
│     - Django Repositories                       │
│     - Gemini Services                           │
│     - Text Extractors                           │
│     - RAG Orchestrator                          │
└─────────────────────────────────────────────────┘
```

## Key Principles

### 1. **Dependency Inversion**
- High-level modules (domain, application) don't depend on low-level modules (infrastructure)
- Both depend on abstractions (ports/interfaces)

### 2. **Single Responsibility**
- Each layer has a clear, single responsibility
- Entities contain business logic
- Use cases orchestrate workflows
- Adapters handle external concerns

### 3. **Testability**
- Domain logic can be tested without frameworks
- Use cases can be tested with mock repositories
- Each layer can be tested independently

### 4. **Framework Independence**
- Core business logic is framework-agnostic
- Django is just an infrastructure detail
- Can easily swap Django for FastAPI, Flask, etc.

## Dependency Injection

The `core/dependencies.py` module provides a simple dependency injection container:

```python
from core.dependencies import (
    get_upload_document_use_case,
    get_process_document_use_case,
    get_ask_question_use_case
)

# In your views
upload_use_case = get_upload_document_use_case()
result = upload_use_case.execute(upload_dto)
```

## Migration from Old Architecture

### Before (Layered Architecture)
```
documents/
  ├── models.py           # Django models + business logic
  ├── views.py            # API + business logic
  ├── services.py         # Mixed concerns
  └── serializers.py      # Data transformation
```

### After (Hexagonal Architecture)
```
core/
  ├── domain/             # Pure business logic
  ├── application/        # Use cases + ports
  └── infrastructure/     # Adapters (Django, Gemini, etc.)
api/
  └── v1/                 # HTTP adapters
```

## Benefits

1. **Maintainability**: Clear separation of concerns
2. **Testability**: Business logic isolated from frameworks
3. **Flexibility**: Easy to swap implementations
4. **Scalability**: Well-defined boundaries for growth
5. **Team Collaboration**: Clear contracts between layers

## Package Manager: UV

The project now uses **uv** instead of pip for faster, more reliable dependency management.

### Key Files
- **`pyproject.toml`**: Project configuration and dependencies
- **`uv.lock`**: Locked dependency versions
- **`Dockerfile`**: Updated to use uv

### Common Commands
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update dependencies
uv lock --upgrade

# Run with uv
uv run python manage.py runserver
```

## Testing Strategy

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=core --cov-report=html

# Run specific layer tests
uv run pytest core/domain/
uv run pytest core/application/
uv run pytest core/infrastructure/
```

## Future Enhancements

1. **Event-Driven Architecture**: Add domain events for decoupling
2. **CQRS**: Separate read and write models
3. **Async Processing**: Add Celery for background tasks
4. **API Versioning**: Multiple API versions side-by-side
5. **GraphQL**: Alternative API layer

## References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [UV Package Manager](https://github.com/astral-sh/uv)
