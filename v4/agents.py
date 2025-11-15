import google.generativeai as genai
from django.conf import settings
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import Graph, StateGraph, END
import operator
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)


class AgentState(TypedDict):
    """State for the multi-agent system"""

    query: str
    conversation_history: List[Dict[str, str]]
    intent: str
    retrieved_chunks: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class RouterAgent:
    """Agent to route queries to appropriate handler"""

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def route(self, state: AgentState) -> AgentState:
        """Determine the intent of the user query"""
        query = state["query"]

        prompt = f"""Analyze the following user query and determine the intent.

Query: {query}

Classify the intent as one of:
- RAG_QUERY: Questions about document content, factual queries
- SUMMARIZE: Requests for summarization (keywords: summarize, summary, خلاصه)
- TRANSLATE: Translation requests (keywords: translate, ترجمه)
- CHECKLIST: Requests for structured lists/checklists (keywords: checklist, list, لیست, چک‌لیست)

Respond with ONLY the intent category, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            intent = response.text.strip().upper()

            # Validate intent
            valid_intents = ["RAG_QUERY", "SUMMARIZE", "TRANSLATE", "CHECKLIST"]
            if intent not in valid_intents:
                intent = "RAG_QUERY"  # Default to RAG

            state["intent"] = intent
            logger.info(f"Routed query to: {intent}")

        except Exception as e:
            logger.error(f"Error in router agent: {str(e)}")
            state["intent"] = "RAG_QUERY"

        return state


class RetrieverAgent:
    """Agent for retrieving relevant document chunks"""

    def __init__(self, retrieval_service):
        self.retrieval_service = retrieval_service

    def retrieve(self, state: AgentState) -> AgentState:
        """Retrieve relevant chunks for the query"""
        query = state["query"]

        try:
            chunks = self.retrieval_service.retrieve(query)
            state["retrieved_chunks"] = chunks
            logger.info(f"Retrieved {len(chunks)} chunks for query")

        except Exception as e:
            logger.error(f"Error in retriever agent: {str(e)}")
            state["retrieved_chunks"] = []

        return state


class ReasoningAgent:
    """Agent for reasoning and answer generation"""

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def reason(self, state: AgentState) -> AgentState:
        """Generate answer based on retrieved chunks"""
        query = state["query"]
        chunks = state["retrieved_chunks"]

        if not chunks:
            state["answer"] = (
                "I don't have enough information in the uploaded documents to answer this question. "
                "Please make sure you've uploaded relevant documents or try rephrasing your question."
            )
            state["citations"] = []
            return state

        # Build context from chunks
        context = "\n\n".join(
            [
                f"[Document: {chunk['document_title']}, Page: {chunk['page']}]\n{chunk['text']}"
                for chunk in chunks
            ]
        )

        prompt = f"""You are a helpful assistant that answers questions based strictly on provided document content.

Context from documents:
{context}

User question: {query}

Instructions:
1. Answer the question based ONLY on the provided context
2. Be concise and accurate
3. If the context doesn't contain enough information, say so
4. Use natural language and be helpful
5. Support bilingual queries (English and Persian)

Answer:"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text

            state["answer"] = answer
            state["citations"] = [
                {
                    "document_id": chunk["document_id"],
                    "document_title": chunk["document_title"],
                    "chunk_index": chunk["chunk_index"],
                    "page": chunk["page"],
                    "snippet": chunk["snippet"],
                }
                for chunk in chunks
            ]

            logger.info("Generated answer with citations")

        except Exception as e:
            logger.error(f"Error in reasoning agent: {str(e)}")
            state["answer"] = "I encountered an error generating the answer. Please try again."
            state["citations"] = []

        return state


class UtilityAgent:
    """Agent for utility tasks (summarization, translation, checklist)"""

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def process(self, state: AgentState) -> AgentState:
        """Process utility tasks"""
        query = state["query"]
        intent = state["intent"]
        chunks = state.get("retrieved_chunks", [])
        conversation_history = state.get("conversation_history", [])

        # Get context from conversation or chunks
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1]
            context = last_message.get("content", "")
        elif chunks:
            context = "\n\n".join([chunk["text"] for chunk in chunks])
        else:
            context = ""

        if intent == "SUMMARIZE":
            answer = self._summarize(query, context)
        elif intent == "TRANSLATE":
            answer = self._translate(query, context)
        elif intent == "CHECKLIST":
            answer = self._generate_checklist(query, context)
        else:
            answer = "I'm not sure how to process this request."

        state["answer"] = answer
        state["citations"] = []
        return state

    def _summarize(self, query: str, context: str) -> str:
        """Generate summary"""
        prompt = f"""Provide a concise summary based on the following content.

Content:
{context}

User request: {query}

Summary:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            return "I encountered an error generating the summary."

    def _translate(self, query: str, context: str) -> str:
        """Translate content"""
        prompt = f"""Translate the following content based on the user's request.

Content:
{context}

User request: {query}

Translation:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in translation: {str(e)}")
            return "I encountered an error performing the translation."

    def _generate_checklist(self, query: str, context: str) -> str:
        """Generate checklist"""
        prompt = f"""Generate a structured checklist based on the following content.

Content:
{context}

User request: {query}

Format the output as a clear, actionable checklist.

Checklist:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in checklist generation: {str(e)}")
            return "I encountered an error generating the checklist."


class MultiAgentOrchestrator:
    """Orchestrator for multi-agent system using LangGraph"""

    def __init__(self, retrieval_service):
        self.router = RouterAgent()
        self.retriever = RetrieverAgent(retrieval_service)
        self.reasoner = ReasoningAgent()
        self.utility = UtilityAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> Graph:
        """Build the LangGraph workflow"""

        # Define the workflow
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self.router.route)
        workflow.add_node("retriever", self.retriever.retrieve)
        workflow.add_node("reasoner", self.reasoner.reason)
        workflow.add_node("utility", self.utility.process)

        # Define conditional routing
        def route_based_on_intent(state: AgentState) -> str:
            intent = state.get("intent", "RAG_QUERY")
            if intent == "RAG_QUERY":
                return "retriever"
            else:
                return "utility"

        # Set entry point
        workflow.set_entry_point("router")

        # Add edges
        workflow.add_conditional_edges(
            "router", route_based_on_intent, {"retriever": "retriever", "utility": "utility"}
        )

        workflow.add_edge("retriever", "reasoner")
        workflow.add_edge("reasoner", END)
        workflow.add_edge("utility", END)

        return workflow.compile()

    def process_query(
        self, query: str, conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process a query through the multi-agent system"""

        if conversation_history is None:
            conversation_history = []

        initial_state: AgentState = {
            "query": query,
            "conversation_history": conversation_history,
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
        }

        try:
            # Run the graph
            result = self.graph.invoke(initial_state)

            return {
                "answer": result["answer"],
                "citations": result["citations"],
                "intent": result["intent"],
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            return {
                "answer": "I encountered an error processing your request. Please try again.",
                "citations": [],
                "intent": "ERROR",
                "metadata": {"error": str(e)},
            }
