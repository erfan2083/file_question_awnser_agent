# 📚 Intelligent Document Question Answering System

A sophisticated document-based Question Answering (QA) system with multi-agent orchestration using LangChain, LangGraph, and Google Gemini API.

## 🌟 Features

- **Multi-Agent Architecture**: Three specialized agents working in harmony
  - **Retriever Agent**: Hybrid search (BM25 + Vector embeddings)
  - **Reasoning Agent**: Chain-of-thought reasoning for accurate answers
  - **Utility Agent**: Translation, summarization, and checklist generation

- **Document Processing**: Support for PDF, DOCX, TXT, and Images (with OCR)
- **Hybrid Retrieval**: Combines keyword and semantic search with reranking
- **Multilingual Support**: English, Spanish, French, German, and Arabic
- **Interactive UI**: Both Streamlit web interface and REST API
- **100% Test Coverage**: Comprehensive test suite with pytest
- **Docker Support**: Fully containerized application

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │  Streamlit Web UI    │    │   FastAPI REST API   │       │
│  └──────────────────────┘    └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Agent Orchestrator                    │
│                      (LangGraph)                             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌────────▼───────┐
│ Retriever      │  │  Reasoning   │  │    Utility     │
│ Agent          │  │  Agent       │  │    Agent       │
│                │  │              │  │                │
│ - Hybrid Search│  │ - Chain of   │  │ - Translation  │
│ - BM25         │  │   Thought    │  │ - Summarization│
│ - Vector DB    │  │ - Answer Gen │  │ - Checklists   │
└────────────────┘  └──────────────┘  └────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│              Document Processing Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │  Loaders    │  │   Chunkers   │  │    Indexers     │    │
│  │ PDF/DOCX/TXT│  │  Overlapping │  │  ChromaDB       │    │
│  │  OCR Images │  │    Chunks    │  │  Embeddings     │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key (free at https://makersuite.google.com/app/apikey)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd document-qa-system
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Running the Application

#### Option 1: Streamlit Web UI
```bash
streamlit run ui/streamlit_app.py
```
Access the UI at http://localhost:8501

#### Option 2: FastAPI REST API
```bash
python -m api.main
```
Access the API at http://localhost:8000
API documentation at http://localhost:8000/docs

#### Option 3: Docker
```bash
cd docker
docker-compose up --build
```
- Streamlit UI: http://localhost:8501
- FastAPI: http://localhost:8000

## 📖 Usage Guide

### 1. Upload Documents

**Via Streamlit:**
- Navigate to "Upload Documents" page
- Select files (PDF, DOCX, TXT, Images)
- Click "Upload and Index"

**Via API:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 2. Ask Questions

**Via Streamlit:**
- Navigate to "Ask Questions" page
- Type your question
- Click "Get Answer"

**Via API:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

### 3. Utility Tasks

**Translation:**
```python
from src.agents import UtilityAgent
from src.models.schemas import UtilityTask

agent = UtilityAgent()
result = agent.execute(
    task=UtilityTask.TRANSLATE,
    text="Hello world",
    target_language="es"
)
```

**Summarization:**
```python
result = agent.execute(
    task=UtilityTask.SUMMARIZE,
    text="Long document text..."
)
```

**Checklist Generation:**
```python
result = agent.execute(
    task=UtilityTask.CHECKLIST,
    text="Document with action items..."
)
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Module
```bash
pytest tests/test_agents/
```

## 📁 Project Structure

```
document-qa-system/
├── src/                         # Source code
│   ├── agents/                  # Agent implementations
│   │   ├── retriever_agent.py
│   │   ├── reasoning_agent.py
│   │   ├── utility_agent.py
│   │   └── orchestrator.py
│   ├── document_processing/     # Document handling
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   └── indexer.py
│   ├── retrieval/               # Retrieval system
│   │   ├── bm25_retriever.py
│   │   ├── vector_retriever.py
│   │   ├── hybrid_search.py
│   │   └── reranker.py
│   ├── models/                  # Data models
│   │   └── schemas.py
│   ├── config/                  # Configuration
│   │   └── settings.py
│   └── utils/                   # Utilities
│       └── helpers.py
├── api/                         # FastAPI application
│   └── main.py
├── ui/                          # Streamlit application
│   └── streamlit_app.py
├── tests/                       # Test suite
├── docker/                      # Docker configuration
├── notebooks/                   # Jupyter notebooks
├── data/                        # Data storage
│   ├── uploads/
│   └── vectorstore/
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 🔧 Configuration

Key configuration parameters in `.env`:

```bash
# API Configuration
GOOGLE_API_KEY=your_api_key_here

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Retrieval
TOP_K_RETRIEVAL=5
RERANK_TOP_K=3
BM25_WEIGHT=0.5
VECTOR_WEIGHT=0.5

# Model Configuration
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/embedding-001
```

## 📊 Performance

- **Retrieval Speed**: < 1 second for most queries
- **Answer Generation**: 2-5 seconds depending on complexity
- **Document Indexing**: ~1 second per page
- **Memory Usage**: ~500MB base + document data

## 🛠️ Development

### Code Quality

The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

### Pre-commit Hooks

All checks run automatically before commits:
```bash
black .
isort .
flake8 src tests
mypy src
pytest
```

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Ensure 100% test coverage
4. Run pre-commit checks
5. Submit pull request

## 📝 API Documentation

### Endpoints

#### Upload Document
```
POST /upload
Content-Type: multipart/form-data
```

#### Ask Question
```
POST /ask
Content-Type: application/json
Body: {"question": "string", "document_id": "optional"}
```

#### Utility Task
```
POST /utility
Content-Type: application/json
Body: {"task": "string", "text": "string", "target_language": "string"}
```

#### List Documents
```
GET /documents
```

#### Delete Document
```
DELETE /documents/{document_id}
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Install all dependencies: `pip install -r requirements.txt`

2. **API Key Errors**
   - Check `.env` file has valid GOOGLE_API_KEY
   - Verify API key at https://makersuite.google.com/

3. **Memory Issues**
   - Reduce CHUNK_SIZE in configuration
   - Lower TOP_K_RETRIEVAL value

4. **Tesseract OCR Errors**
   - Install tesseract: `sudo apt-get install tesseract-ocr`

## 📦 Dependencies

### Core
- langchain==0.1.0
- langchain-google-genai==0.0.6
- langgraph==0.0.20
- google-generativeai==0.3.2

### Document Processing
- pypdf2==3.0.1
- python-docx==1.1.0
- pytesseract==0.3.10

### Retrieval
- chromadb==0.4.22
- rank-bm25==0.2.2
- sentence-transformers==2.2.2

### Web Framework
- fastapi==0.109.0
- streamlit==1.30.0

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

Your Team - AI Engineering Project

## 🙏 Acknowledgments

- Anthropic Claude for development assistance
- LangChain and LangGraph teams
- Google for Gemini API
- Open source community

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using LangChain, LangGraph, and Google Gemini**
