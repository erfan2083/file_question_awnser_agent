# 🧪 Testing Guide

## Quick Test Commands

### Run All Tests
```bash
cd document-qa-system
pytest
```

### Run with Coverage Report
```bash
pytest --cov=src --cov-report=html --cov-report=term
# View HTML report: open htmlcov/index.html
```

### Run Specific Test Modules
```bash
# Test utilities
pytest tests/test_utils.py -v

# Test agents (when created)
pytest tests/test_agents/ -v

# Test document processing
pytest tests/test_document_processing/ -v

# Test retrieval
pytest tests/test_retrieval/ -v
```

### Run with Detailed Output
```bash
pytest -vv --tb=short
```

## Manual Testing Guide

### Test 1: Document Upload (2 minutes)

**Steps:**
1. Start UI: `streamlit run ui/streamlit_app.py`
2. Navigate to "Upload Documents"
3. Upload a test PDF/TXT file
4. Verify success message and chunk count

**Expected Result:**
✅ Document uploaded successfully  
✅ Shows number of chunks created  
✅ Document appears in list

### Test 2: Question Answering (3 minutes)

**Steps:**
1. With documents uploaded
2. Navigate to "Ask Questions"
3. Ask: "What is this document about?"
4. Click "Get Answer"

**Expected Result:**
✅ Answer appears within 5 seconds  
✅ Source citations are shown  
✅ Answer is relevant to document

### Test 3: Translation (2 minutes)

**Steps:**
1. Navigate to "Utility Tasks"
2. Select "Translate"
3. Enter text: "Hello, how are you?"
4. Select target language: Spanish
5. Click "Execute Task"

**Expected Result:**
✅ Shows Spanish translation  
✅ Translation is accurate  
✅ Maintains original meaning

### Test 4: API Endpoints (3 minutes)

**Test Health Endpoint:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "service": "document-qa-system"}
```

**Test Upload:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf"
# Expected: JSON with document_id and num_chunks
```

**Test Question:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AI?"}'
# Expected: JSON with answer and sources
```

## Test Data

### Sample Questions to Test
1. "What is the main topic of the document?"
2. "Summarize the key points"
3. "What are the important dates mentioned?"
4. "Who are the main people or organizations discussed?"
5. "What conclusions are drawn?"

### Sample Documents for Testing
- **Technical**: API documentation, research papers
- **Business**: Reports, presentations
- **General**: Articles, books, essays
- **Mixed**: Combined text and tables

## Automated Testing

### Pre-commit Hook Test
```bash
# Trigger pre-commit hooks
git add .
git commit -m "test commit"
# Should run: black, isort, flake8, mypy, pytest
```

### Continuous Testing
```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw
```

## Performance Testing

### Load Test Documents
```python
# Create test script
import time
from src.document_processing import load_document, chunk_document, DocumentIndexer

start = time.time()
text, metadata = load_document("large_document.pdf")
chunks = chunk_document(text, metadata)
indexer = DocumentIndexer()
indexer.index_chunks(chunks, metadata)
print(f"Time taken: {time.time() - start:.2f} seconds")
```

### Query Performance Test
```python
from src.agents import MultiAgentOrchestrator
import time

orchestrator = MultiAgentOrchestrator()
queries = [
    "What is the main topic?",
    "Summarize the document",
    "What are the key findings?"
]

for query in queries:
    start = time.time()
    answer = orchestrator.answer_question(query)
    print(f"{query}: {time.time() - start:.2f}s")
```

## Integration Testing

### Full Pipeline Test
```python
# Test complete workflow
from src.document_processing import load_document, chunk_document
from src.agents import MultiAgentOrchestrator

# 1. Load document
text, metadata = load_document("test.pdf")
print("✓ Document loaded")

# 2. Chunk document
chunks = chunk_document(text, metadata)
print(f"✓ Created {len(chunks)} chunks")

# 3. Initialize system
orchestrator = MultiAgentOrchestrator()
retriever_agent, _, _ = orchestrator.get_agents()
indexer = retriever_agent.get_retriever().get_retrievers()[0].get_indexer()
print("✓ System initialized")

# 4. Index document
indexer.index_chunks(chunks, metadata)
print("✓ Document indexed")

# 5. Ask question
answer = orchestrator.answer_question("What is this about?")
print(f"✓ Answer: {answer.answer[:100]}...")

print("\n✅ Full pipeline test passed!")
```

## Docker Testing

### Test Docker Build
```bash
cd docker
docker-compose build
# Should complete without errors
```

### Test Docker Services
```bash
docker-compose up -d
# Wait 10 seconds
curl http://localhost:8000/health
curl http://localhost:8501
docker-compose down
```

## Troubleshooting Tests

### Common Test Failures

**Import Errors:**
```bash
# Fix: Ensure you're in project root
cd document-qa-system
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

**API Key Errors in Tests:**
```bash
# Fix: Set test API key
export GOOGLE_API_KEY="test_key"
pytest
```

**ChromaDB Errors:**
```bash
# Fix: Clear test database
rm -rf data/test_vectorstore/
pytest
```

## Coverage Goals

Target: **100% Code Coverage**

Current focus areas:
- ✅ Utilities: 100%
- 🔄 Document Processing: 95%+
- 🔄 Retrieval: 95%+
- 🔄 Agents: 90%+
- 🔄 API: 85%+

### View Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html  # or: firefox htmlcov/index.html
```

## Test Checklist

Before submitting:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Coverage >95%
- [ ] Pre-commit hooks pass
- [ ] Manual tests successful
- [ ] Docker builds successfully
- [ ] API endpoints respond correctly
- [ ] UI loads and functions
- [ ] Documentation updated

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=src --cov-fail-under=95
```

## Success Criteria

### Passing Tests Should Show:
✅ All tests pass (green dots)  
✅ Coverage >95%  
✅ No flake8 warnings  
✅ No mypy errors  
✅ Clean pre-commit hooks  
✅ Docker builds successfully  
✅ API responds correctly  
✅ UI loads properly

### Quality Metrics:
- Response time: <5s for questions
- Indexing: <2s per document
- Memory usage: <1GB
- Error rate: <1%

---

**Remember:** Good tests = Good code = Successful project!
