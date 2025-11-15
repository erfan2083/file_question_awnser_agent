import pytest
from rag.retrieval import RetrievalService
from rag.agents import (
    RouterAgent,
    RetrieverAgent,
    ReasoningAgent,
    UtilityAgent,
    MultiAgentOrchestrator,
    AgentState,
)


@pytest.mark.django_db
class TestRetrievalService:
    """Tests for RetrievalService"""

    def test_retrieve_with_no_documents(self):
        service = RetrievalService()
        results = service.retrieve("test query")
        assert results == []

    def test_retrieve_with_documents(self, sample_document, sample_chunk):
        service = RetrievalService()
        results = service.retrieve("sample text")
        assert isinstance(results, list)

    def test_cosine_similarity(self):
        service = RetrievalService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = service._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)


@pytest.mark.django_db
class TestRouterAgent:
    """Tests for RouterAgent"""

    def test_route_rag_query(self):
        agent = RouterAgent()
        state: AgentState = {
            "query": "What is the document about?",
            "conversation_history": [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
        }
        result = agent.route(state)
        assert "intent" in result
        assert result["intent"] in [
            "RAG_QUERY",
            "SUMMARIZE",
            "TRANSLATE",
            "CHECKLIST",
        ]


@pytest.mark.django_db
class TestRetrieverAgent:
    """Tests for RetrieverAgent"""

    def test_retrieve(self, sample_document, sample_chunk):
        retrieval_service = RetrievalService()
        agent = RetrieverAgent(retrieval_service)

        state: AgentState = {
            "query": "sample text",
            "conversation_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
        }
        result = agent.retrieve(state)
        assert "retrieved_chunks" in result
        assert isinstance(result["retrieved_chunks"], list)


@pytest.mark.django_db
class TestReasoningAgent:
    """Tests for ReasoningAgent"""

    def test_reason_with_chunks(self):
        agent = ReasoningAgent()
        state: AgentState = {
            "query": "What is this about?",
            "conversation_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [
                {
                    "document_id": 1,
                    "document_title": "Test",
                    "chunk_index": 0,
                    "page": 1,
                    "text": "This is about testing",
                    "snippet": "This is about testing",
                }
            ],
            "answer": "",
            "citations": [],
            "metadata": {},
        }
        result = agent.reason(state)
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "citations" in result

    def test_reason_without_chunks(self):
        agent = ReasoningAgent()
        state: AgentState = {
            "query": "What is this about?",
            "conversation_history": [],
            "intent": "RAG_QUERY",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
        }
        result = agent.reason(state)
        assert "answer" in result
        assert "don't have enough information" in result["answer"].lower()


@pytest.mark.django_db
class TestUtilityAgent:
    """Tests for UtilityAgent"""

    def test_summarize(self):
        agent = UtilityAgent()
        context = "This is a long document with lots of content."
        answer = agent._summarize("Summarize this", context)
        assert isinstance(answer, str)
        assert len(answer) > 0


@pytest.mark.django_db
class TestMultiAgentOrchestrator:
    """Tests for MultiAgentOrchestrator"""

    def test_orchestrator_init(self):
        retrieval_service = RetrievalService()
        orchestrator = MultiAgentOrchestrator(retrieval_service)
        assert orchestrator.graph is not None

    def test_process_query(self, sample_document, sample_chunk):
        retrieval_service = RetrievalService()
        orchestrator = MultiAgentOrchestrator(retrieval_service)

        result = orchestrator.process_query("What is this document about?")
        assert "answer" in result
        assert "citations" in result
        assert "intent" in result
