"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import MultiAgentOrchestrator, ReasoningAgent, RetrieverAgent, UtilityAgent
from src.config.settings import settings
from src.document_processing import DocumentChunker, DocumentIndexer, DocumentLoader
from src.models.schemas import (
    DocumentChunk,
    DocumentFormat,
    DocumentMetadata,
    UtilityTask,
)
from src.retrieval import BM25Retriever, HybridRetriever, VectorRetriever

# Test environment variables
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "test_api_key")
os.environ["CHROMA_PERSIST_DIRECTORY"] = "./data/test_vectorstore"
os.environ["LOG_LEVEL"] = "ERROR"


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Artificial Intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural 
    intelligence displayed by humans. AI research has been defined as the field of study of intelligent 
    agents, which refers to any system that perceives its environment and takes actions that maximize 
    its chance of achieving its goals. The term "artificial intelligence" had previously been used to 
    describe machines that mimic and display "human" cognitive skills that are associated with the 
    human mind, such as "learning" and "problem-solving". This definition has since been rejected by 
    major AI researchers who now describe AI in terms of rationality and acting rationally, which does 
    not limit how intelligence can be articulated.
    """


@pytest.fixture
def sample_document_metadata():
    """Sample document metadata."""
    return DocumentMetadata(
        document_id="test_doc_123",
        filename="test_document.txt",
        format=DocumentFormat.TXT,
        file_size=1000,
        num_chunks=0,
    )


@pytest.fixture
def sample_chunks(sample_text, sample_document_metadata):
    """Sample document chunks."""
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    return chunker.chunk_text(sample_text, sample_document_metadata)


@pytest.fixture
def document_loader():
    """Document loader instance."""
    return DocumentLoader()


@pytest.fixture
def document_chunker():
    """Document chunker instance."""
    return DocumentChunker()


@pytest.fixture
def document_indexer():
    """Document indexer instance."""
    return DocumentIndexer()


@pytest.fixture
def bm25_retriever():
    """BM25 retriever instance."""
    return BM25Retriever()


@pytest.fixture
def vector_retriever():
    """Vector retriever instance."""
    return VectorRetriever()


@pytest.fixture
def hybrid_retriever():
    """Hybrid retriever instance."""
    return HybridRetriever()


@pytest.fixture
def retriever_agent():
    """Retriever agent instance."""
    return RetrieverAgent()


@pytest.fixture
def reasoning_agent():
    """Reasoning agent instance."""
    return ReasoningAgent()


@pytest.fixture
def utility_agent():
    """Utility agent instance."""
    return UtilityAgent()


@pytest.fixture
def orchestrator():
    """Multi-agent orchestrator instance."""
    return MultiAgentOrchestrator()


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    # Create a simple text file instead for testing
    pdf_path.write_text("This is a test PDF content.")
    return pdf_path


@pytest.fixture
def sample_txt_path(tmp_path):
    """Create a sample TXT file for testing."""
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("This is a test TXT content. It has multiple sentences. This is the third sentence.")
    return txt_path


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup code here if needed
    pass
