"""
Comprehensive tests for RAG services and multi-agent orchestration.
Covers agents, retrieval, and orchestration logic.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np

from rag.services import RAGOrchestrator, AgentState


# ============================================================
# RAG Orchestrator Tests
# ============================================================

@pytest.mark.django_db
class TestRAGOrchestrator:
    """Tests for RAGOrchestrator."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_orchestrator_initialization(self, mock_llm, mock_genai):
        """Test orchestrator initialization."""
        orchestrator = RAGOrchestrator()
        
        assert orchestrator.graph is not None
        mock_genai.assert_called_once()
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_router_agent_rag_query(self, mock_llm, mock_genai):
        """Test router agent classifies RAG queries."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "What is machine learning?",
            "chat_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._router_agent(state)
        
        assert result["intent"] == "RAG_QUERY"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_router_agent_summarize(self, mock_llm, mock_genai):
        """Test router agent classifies summarize requests."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Summarize this document",
            "chat_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._router_agent(state)
        
        assert result["intent"] == "SUMMARIZE"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_router_agent_translate(self, mock_llm, mock_genai):
        """Test router agent classifies translation requests."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Translate this to Persian",
            "chat_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._router_agent(state)
        
        assert result["intent"] == "TRANSLATE"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_router_agent_checklist(self, mock_llm, mock_genai):
        """Test router agent classifies checklist requests."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Create a checklist from this",
            "chat_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._router_agent(state)
        
        assert result["intent"] == "CHECKLIST"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_router_agent_persian_summarize(self, mock_llm, mock_genai):
        """Test router agent with Persian summarize command."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "خلاصه این متن را بده",
            "chat_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._router_agent(state)
        
        assert result["intent"] == "SUMMARIZE"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_route_decision_rag(self, mock_llm, mock_genai):
        """Test route decision for RAG queries."""
        orchestrator = RAGOrchestrator()
        
        state = {"intent": "RAG_QUERY"}
        result = orchestrator._route_decision(state)
        
        assert result == "retriever"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_route_decision_utility(self, mock_llm, mock_genai):
        """Test route decision for utility tasks."""
        orchestrator = RAGOrchestrator()
        
        for intent in ["SUMMARIZE", "TRANSLATE", "CHECKLIST"]:
            state = {"intent": intent}
            result = orchestrator._route_decision(state)
            assert result == "utility"


@pytest.mark.django_db
class TestRetrieverAgent:
    """Tests for Retriever Agent."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    @patch('rag.services.genai.embed_content')
    def test_retriever_no_documents(self, mock_embed, mock_llm, mock_genai):
        """Test retriever when no documents are available."""
        mock_embed.return_value = {'embedding': [0.1] * 768}
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "What is AI?",
            "chat_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._retriever_agent(state)
        
        assert result["retrieved_chunks"] == []
        assert "No documents available" in result["error"]
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    @patch('rag.services.genai.embed_content')
    def test_retriever_with_chunks(self, mock_embed, mock_llm, mock_genai, sample_document, multiple_chunks):
        """Test retriever with available chunks."""
        mock_embed.return_value = {'embedding': [0.1] * 768}
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "What is AI?",
            "chat_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._retriever_agent(state)
        
        assert len(result["retrieved_chunks"]) > 0
        assert result["error"] == ""


@pytest.mark.django_db
class TestReasoningAgent:
    """Tests for Reasoning Agent."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_reasoning_no_chunks(self, mock_llm, mock_genai):
        """Test reasoning agent when no chunks available."""
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "What is AI?",
            "chat_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._reasoning_agent(state)
        
        assert "couldn't find" in result["answer"].lower()
        assert result["citations"] == []
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_reasoning_with_chunks(self, mock_llm_class, mock_genai):
        """Test reasoning agent with chunks."""
        # Setup mock
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="AI is artificial intelligence based on the documents."
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "What is AI?",
            "chat_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [
                {
                    "chunk_id": 1,
                    "document_id": 1,
                    "document_title": "AI Guide",
                    "chunk_index": 0,
                    "page_number": 1,
                    "text": "Artificial Intelligence is the simulation of human intelligence.",
                    "score": 0.9
                }
            ],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._reasoning_agent(state)
        
        assert result["answer"] != ""
        assert len(result["citations"]) > 0


@pytest.mark.django_db
class TestUtilityAgent:
    """Tests for Utility Agent."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_utility_summarize(self, mock_llm_class, mock_genai):
        """Test utility agent summarization."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="This is a summary of the content."
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Summarize: Long text here...",
            "chat_history": [],
            "intent": "SUMMARIZE",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._utility_agent(state)
        
        assert result["answer"] != ""
        assert result["metadata"]["agent_type"] == "utility"
        assert result["metadata"]["utility_function"] == "summarize"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_utility_translate(self, mock_llm_class, mock_genai):
        """Test utility agent translation."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="این یک ترجمه است."
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Translate to Persian: Hello world",
            "chat_history": [],
            "intent": "TRANSLATE",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._utility_agent(state)
        
        assert result["metadata"]["utility_function"] == "translate"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_utility_checklist(self, mock_llm_class, mock_genai):
        """Test utility agent checklist generation."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="1. Item one\n2. Item two\n3. Item three"
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        state = {
            "query": "Create checklist: Things to do",
            "chat_history": [],
            "intent": "CHECKLIST",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        result = orchestrator._utility_agent(state)
        
        assert result["metadata"]["utility_function"] == "checklist"


# ============================================================
# Search Algorithm Tests
# ============================================================

@pytest.mark.django_db
class TestSearchAlgorithms:
    """Tests for search algorithms."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_vector_search(self, mock_llm, mock_genai, sample_document, multiple_chunks):
        """Test vector similarity search."""
        orchestrator = RAGOrchestrator()
        
        query_embedding = [0.1] * 768
        chunks = sample_document.chunks.all()
        
        results = orchestrator._vector_search(query_embedding, chunks)
        
        assert len(results) > 0
        assert all(isinstance(r, tuple) for r in results)
        # Results should be sorted by similarity (descending)
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_bm25_search(self, mock_llm, mock_genai, sample_document, multiple_chunks):
        """Test BM25 keyword search."""
        orchestrator = RAGOrchestrator()
        
        chunks = sample_document.chunks.all()
        
        results = orchestrator._bm25_search("test content", chunks)
        
        assert len(results) > 0
        assert all(isinstance(r, tuple) for r in results)
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_combine_and_rerank(self, mock_llm, mock_genai, sample_document, multiple_chunks):
        """Test combining and reranking results."""
        orchestrator = RAGOrchestrator()
        
        chunks = list(sample_document.chunks.all())
        
        # Create mock results
        vector_results = [(chunk, 0.9 - i * 0.1) for i, chunk in enumerate(chunks)]
        bm25_results = [(chunk, 5.0 - i * 0.5) for i, chunk in enumerate(chunks)]
        
        combined = orchestrator._combine_and_rerank(
            vector_results,
            bm25_results,
            "test query",
            alpha=0.7
        )
        
        assert len(combined) > 0
        # Results should be sorted by combined score
        scores = [r[1] for r in combined]
        assert scores == sorted(scores, reverse=True)
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_combine_empty_results(self, mock_llm, mock_genai):
        """Test combining empty results."""
        orchestrator = RAGOrchestrator()
        
        combined = orchestrator._combine_and_rerank([], [], "query")
        
        assert combined == []


# ============================================================
# Integration Tests
# ============================================================

@pytest.mark.django_db
class TestRAGIntegration:
    """Integration tests for RAG pipeline."""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    @patch('rag.services.genai.embed_content')
    def test_full_rag_pipeline(self, mock_embed, mock_llm_class, mock_genai, sample_document, multiple_chunks):
        """Test complete RAG pipeline."""
        mock_embed.return_value = {'embedding': [0.1] * 768}
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="Based on the documents, this is the answer."
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        result = orchestrator.process_query(
            "What is the content about?",
            chat_history=[]
        )
        
        assert "answer" in result
        assert "citations" in result
        assert "metadata" in result
        assert result["error"] == ""
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_utility_pipeline(self, mock_llm_class, mock_genai):
        """Test utility pipeline."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="Here is the summary."
        )
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        result = orchestrator.process_query(
            "Summarize this text",
            chat_history=[]
        )
        
        assert result["answer"] != ""
        assert result["metadata"].get("intent") == "SUMMARIZE"
    
    @patch('rag.services.genai.configure')
    @patch('rag.services.ChatGoogleGenerativeAI')
    def test_error_handling(self, mock_llm_class, mock_genai):
        """Test error handling in pipeline."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm_instance
        
        orchestrator = RAGOrchestrator()
        
        result = orchestrator.process_query(
            "Summarize this",
            chat_history=[]
        )
        
        # Should handle error gracefully
        assert "error" in result
