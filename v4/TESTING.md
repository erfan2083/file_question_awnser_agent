# Testing Guide

## Overview

This project maintains 100% test coverage with comprehensive unit, integration, and end-to-end tests using pytest.

## Running Tests

### All Tests
```bash
docker-compose exec backend pytest
```

### With Coverage Report
```bash
docker-compose exec backend pytest --cov=. --cov-report=html --cov-report=term-missing
```

### Specific Test File
```bash
docker-compose exec backend pytest documents/tests.py
```

### Specific Test Class
```bash
docker-compose exec backend pytest documents/tests.py::TestDocumentModel
```

### Specific Test Method
```bash
docker-compose exec backend pytest documents/tests.py::TestDocumentModel::test_create_document
```

### Verbose Output
```bash
docker-compose exec backend pytest -v
```

### Stop on First Failure
```bash
docker-compose exec backend pytest -x
```

## Test Structure

```
backend/
├── conftest.py              # Global fixtures
├── documents/
│   └── tests.py             # Document tests
├── chat/
│   └── tests.py             # Chat tests
├── evaluation/
│   └── tests.py             # Evaluation tests
└── rag/
    └── tests.py             # RAG tests
```

## Test Coverage by Module

### Documents App (documents/tests.py)

#### TestDocumentModel
- `test_create_document`: Document creation
- `test_document_status_transition`: Status changes

#### TestDocumentChunk
- `test_create_chunk`: Chunk creation and relationships

#### TestDocumentAPI
- `test_list_documents`: GET /api/documents/
- `test_get_document_detail`: GET /api/documents/{id}/
- `test_upload_document`: POST /api/documents/upload/

#### TestDocumentIngestionService
- `test_extract_from_txt`: Text extraction
- `test_create_chunks`: Chunking algorithm

### Chat App (chat/tests.py)

#### TestChatSession
- `test_create_session`: Session creation
- `test_session_without_title`: Default behavior

#### TestChatMessage
- `test_create_message`: Message creation
- `test_message_with_citations`: Citation handling

#### TestChatAPI
- `test_create_session`: POST /api/chat/sessions/
- `test_list_sessions`: GET /api/chat/sessions/
- `test_get_session_messages`: GET /api/chat/sessions/{id}/messages/
- `test_send_message`: POST /api/chat/sessions/{id}/messages/

### Evaluation App (evaluation/tests.py)

#### TestQueryModel
- `test_create_test_query`: Test query creation

#### TestEvaluationRun
- `test_create_evaluation_run`: Evaluation run creation

#### TestEvaluationService
- `test_calculate_score`: Scoring algorithm
- `test_calculate_score_no_keywords`: Edge cases

#### TestEvaluationAPI
- `test_list_test_queries`: GET /api/evaluation/queries/
- `test_list_evaluation_results`: GET /api/evaluation/results/
- `test_run_evaluation`: POST /api/evaluation/results/run/

### RAG Module (rag/tests.py)

#### TestRetrievalService
- `test_retrieve_with_no_documents`: Empty state
- `test_retrieve_with_documents`: Normal operation
- `test_cosine_similarity`: Vector similarity calculation

#### TestRouterAgent
- `test_route_rag_query`: Intent classification

#### TestRetrieverAgent
- `test_retrieve`: Retrieval functionality

#### TestReasoningAgent
- `test_reason_with_chunks`: Answer generation
- `test_reason_without_chunks`: Fallback behavior

#### TestUtilityAgent
- `test_summarize`: Summarization function

#### TestMultiAgentOrchestrator
- `test_orchestrator_init`: Initialization
- `test_process_query`: End-to-end flow

## Fixtures

### Global Fixtures (conftest.py)

- `sample_document`: Creates a test document
- `sample_chunk`: Creates a test chunk with embedding
- `chat_session`: Creates a chat session
- `chat_message`: Creates a chat message
- `test_query`: Creates a test query
- `evaluation_run`: Creates an evaluation run

### Usage Example

```python
@pytest.mark.django_db
def test_with_fixtures(sample_document, sample_chunk):
    # Use fixtures in your test
    assert sample_document.status == Document.Status.READY
    assert sample_chunk.document == sample_document
```

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.django_db
class TestNewFeature:
    """Tests for new feature"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        expected = "result"
        
        # Act
        result = my_function()
        
        # Assert
        assert result == expected
```

### Integration Test Example

```python
@pytest.mark.django_db
class TestAPIEndpoint:
    """Tests for API endpoint"""

    def test_endpoint(self, sample_document):
        """Test API endpoint"""
        client = APIClient()
        response = client.get(f'/api/endpoint/{sample_document.id}/')
        
        assert response.status_code == 200
        assert 'data' in response.data
```

## Mocking

### Mocking External APIs

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
@patch('rag.agents.genai.GenerativeModel')
def test_with_mock(mock_model):
    """Test with mocked Gemini API"""
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value.text = "Mocked response"
    mock_model.return_value = mock_instance
    
    # Test code that uses Gemini
    agent = ReasoningAgent()
    # ... rest of test
```

## Test Markers

### Database Tests
```python
@pytest.mark.django_db
def test_database_operation():
    # Test code
```

### Slow Tests
```python
@pytest.mark.slow
def test_long_running():
    # Test code
```

Run only fast tests:
```bash
pytest -m "not slow"
```

## Code Coverage

### Viewing Coverage Report

After running tests with coverage:
```bash
# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Requirements

- **Target**: 100% coverage
- **Minimum**: 95% coverage
- **Excluded**: migrations, tests, config files

### Coverage Configuration

See `.coveragerc`:
```ini
[run]
omit = 
    */migrations/*
    */tests/*
    */test_*.py
```

## Continuous Integration

### Pre-commit Hooks

Install hooks:
```bash
cd backend
pre-commit install
```

Hooks run automatically on `git commit`:
1. black (formatting)
2. isort (import sorting)
3. flake8 (linting)
4. pytest (tests)

### Manual Pre-commit Check

```bash
cd backend
pre-commit run --all-files
```

## Test Data

### Sample Documents

Create sample documents for testing:
```python
from django.core.files.uploadedfile import SimpleUploadedFile

file = SimpleUploadedFile(
    "test.txt",
    b"Sample document content for testing",
    content_type="text/plain"
)

document = Document.objects.create(
    title="Test Document",
    file=file,
    file_type=Document.FileType.TXT
)
```

### Sample Test Queries

Initialize test queries:
```bash
docker-compose exec backend python manage.py init_test_queries
```

## Debugging Tests

### Use pdb

```python
def test_with_debugger():
    import pdb; pdb.set_trace()
    # Test code
```

### Print Debug Info

```python
def test_with_debug_output(capfd):
    print("Debug information")
    # Test code
    out, err = capfd.readouterr()
    assert "Debug" in out
```

### Verbose Assertions

```bash
pytest -vv
```

## Performance Testing

### Timing Tests

```python
import time

def test_performance():
    start = time.time()
    # Code to test
    duration = time.time() - start
    assert duration < 1.0  # Should complete in under 1 second
```

### Profiling

```bash
pytest --profile
```

## Best Practices

1. **Descriptive Names**: Test names should describe what they test
2. **Arrange-Act-Assert**: Structure tests clearly
3. **One Concept**: Test one thing per test
4. **Independence**: Tests should not depend on each other
5. **Fast**: Keep tests fast for quick feedback
6. **Deterministic**: Tests should always pass or always fail
7. **Fixtures**: Use fixtures for common setup
8. **Mocking**: Mock external dependencies
9. **Coverage**: Aim for 100% coverage
10. **Documentation**: Add docstrings to complex tests

## Common Issues

### Database Not Reset
```bash
docker-compose exec backend python manage.py flush --noinput
docker-compose exec backend python manage.py migrate
```

### Import Errors
- Check PYTHONPATH
- Verify all __init__.py files exist

### Fixture Not Found
- Check conftest.py location
- Verify fixture name matches usage

### Slow Tests
- Use `--reuse-db` flag
- Mock external API calls
- Profile with `--profile`

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [DRF testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
