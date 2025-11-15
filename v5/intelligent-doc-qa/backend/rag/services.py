"""
RAG service with multi-agent orchestration using LangGraph.
"""

from typing import List, Dict, Any, TypedDict, Annotated
import operator
from datetime import datetime

import google.generativeai as genai
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from rank_bm25 import BM25Okapi
import numpy as np

from documents.models import DocumentChunk


class AgentState(TypedDict):
    """State shared across all agents in the graph."""
    query: str
    chat_history: List[Dict[str, str]]
    intent: str  # RAG_QUERY, SUMMARIZE, TRANSLATE, CHECKLIST
    retrieved_chunks: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: str


class RAGOrchestrator:
    """Multi-agent RAG orchestration using LangGraph."""
    
    def __init__(self):
        """Initialize the RAG orchestrator."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        self.top_k = settings.TOP_K_RETRIEVAL
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph multi-agent workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self._router_agent)
        workflow.add_node("retriever", self._retriever_agent)
        workflow.add_node("reasoner", self._reasoning_agent)
        workflow.add_node("utility", self._utility_agent)
        
        # Define edges
        workflow.set_entry_point("router")
        
        # Router decides next step
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "retriever": "retriever",
                "utility": "utility",
                "end": END
            }
        )
        
        # Retriever always goes to reasoner
        workflow.add_edge("retriever", "reasoner")
        
        # Reasoner and utility end the flow
        workflow.add_edge("reasoner", END)
        workflow.add_edge("utility", END)
        
        return workflow.compile()
    
    def process_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent pipeline.
        
        Args:
            query: User's question
            chat_history: Previous conversation messages
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        # Initialize state
        initial_state = {
            "query": query,
            "chat_history": chat_history or [],
            "intent": "",
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "metadata": {},
            "error": ""
        }
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            return {
                "answer": final_state.get("answer", ""),
                "citations": final_state.get("citations", []),
                "metadata": final_state.get("metadata", {}),
                "error": final_state.get("error", "")
            }
        except Exception as e:
            return {
                "answer": "",
                "citations": [],
                "metadata": {},
                "error": str(e)
            }
    
    def _router_agent(self, state: AgentState) -> AgentState:
        """
        Router agent: classify user intent.
        
        Determines whether the query is:
        - RAG_QUERY: Standard question answering
        - SUMMARIZE: Summarization request
        - TRANSLATE: Translation request
        - CHECKLIST: Checklist generation
        """
        query = state["query"].lower()
        
        # Simple intent classification (can be enhanced with LLM)
        if any(keyword in query for keyword in [
            "summarize", "summary", "خلاصه", "خلاصه کن", "خلاصه‌اش کن"
        ]):
            state["intent"] = "SUMMARIZE"
        elif any(keyword in query for keyword in [
            "translate", "ترجمه", "به انگلیسی", "به فارسی", "translation"
        ]):
            state["intent"] = "TRANSLATE"
        elif any(keyword in query for keyword in [
            "checklist", "چک‌لیست", "چک لیست", "list", "tasks", "کارها"
        ]):
            state["intent"] = "CHECKLIST"
        else:
            state["intent"] = "RAG_QUERY"
        
        state["metadata"]["intent"] = state["intent"]
        return state
    
    def _route_decision(self, state: AgentState) -> str:
        """Decide which agent to route to based on intent."""
        intent = state["intent"]
        
        if intent == "RAG_QUERY":
            return "retriever"
        elif intent in ["SUMMARIZE", "TRANSLATE", "CHECKLIST"]:
            return "utility"
        else:
            return "end"
    
    def _retriever_agent(self, state: AgentState) -> AgentState:
        """
        Retriever agent: find relevant document chunks.
        
        Uses hybrid search (vector + BM25) with reranking.
        """
        query = state["query"]
        
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Get all chunks from ready documents
            all_chunks = DocumentChunk.objects.filter(
                document__status='READY'
            ).select_related('document')
            
            if not all_chunks.exists():
                state["error"] = "No documents available for search"
                state["retrieved_chunks"] = []
                return state
            
            # Vector similarity search
            vector_results = self._vector_search(query_embedding, all_chunks)
            
            # BM25 keyword search
            bm25_results = self._bm25_search(query, all_chunks)
            
            # Combine and rerank
            combined_results = self._combine_and_rerank(
                vector_results,
                bm25_results,
                query
            )
            
            # Take top-k
            top_chunks = combined_results[:self.top_k]
            
            # Format chunks
            retrieved_chunks = []
            for chunk, score in top_chunks:
                retrieved_chunks.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document.id,
                    "document_title": chunk.document.title,
                    "chunk_index": chunk.index,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "score": float(score)
                })
            
            state["retrieved_chunks"] = retrieved_chunks
            state["metadata"]["num_retrieved"] = len(retrieved_chunks)
            
        except Exception as e:
            state["error"] = f"Retrieval error: {str(e)}"
            state["retrieved_chunks"] = []
        
        return state
    
    def _reasoning_agent(self, state: AgentState) -> AgentState:
        """
        Reasoning agent: generate answer with chain-of-thought.
        
        Synthesizes information from retrieved chunks and provides citations.
        """
        query = state["query"]
        chunks = state["retrieved_chunks"]
        
        if not chunks:
            state["answer"] = (
                "I couldn't find relevant information in the uploaded documents "
                "to answer your question. Could you please rephrase or ask something else?"
            )
            state["citations"] = []
            return state
        
        # Prepare context from chunks
        context_parts = []
        for idx, chunk in enumerate(chunks):
            context_parts.append(
                f"[Document {idx+1}: {chunk['document_title']}, "
                f"Page {chunk['page_number'] or 'N/A'}]\n{chunk['text']}\n"
            )
        
        context = "\n\n".join(context_parts)
        
        # Create prompt with chain-of-thought
        prompt = f"""You are a helpful AI assistant that answers questions based strictly on the provided document context.

Context from documents:
{context}

User Question: {query}

Instructions:
1. Analyze the provided context carefully
2. Generate a concise, accurate answer based ONLY on the information in the context
3. If the context doesn't contain enough information, say so
4. Include specific references to which documents support your answer
5. Be clear and direct in your response

Answer:"""
        
        try:
            # Generate response using Gemini
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(prompt)
            answer = response.text
            
            # Generate citations
            citations = []
            for chunk in chunks:
                citations.append({
                    "document_id": chunk["document_id"],
                    "document_title": chunk["document_title"],
                    "chunk_index": chunk["chunk_index"],
                    "page": chunk["page_number"],
                    "snippet": chunk["text"][:200] + "..."
                })
            
            state["answer"] = answer
            state["citations"] = citations
            state["metadata"]["agent_type"] = "reasoning"
            
        except Exception as e:
            state["error"] = f"Reasoning error: {str(e)}"
            state["answer"] = "I encountered an error while generating the answer."
            state["citations"] = []
        
        return state
    
    def _utility_agent(self, state: AgentState) -> AgentState:
        """
        Utility agent: handle summarization, translation, checklist generation.
        """
        query = state["query"]
        intent = state["intent"]
        
        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            if intent == "SUMMARIZE":
                prompt = f"""Summarize the following text concisely:

{query}

Provide a clear, concise summary in the same language as the original text."""
                
            elif intent == "TRANSLATE":
                # Detect source and target language
                if any(char for char in query if ord(char) > 1000):  # Persian chars
                    prompt = f"""Translate the following Persian text to English:

{query}

Provide only the English translation."""
                else:
                    prompt = f"""Translate the following English text to Persian:

{query}

Provide only the Persian translation."""
            
            elif intent == "CHECKLIST":
                prompt = f"""Based on the following text, create a structured checklist or task list:

{query}

Format the output as a clear, actionable checklist."""
            
            else:
                state["error"] = f"Unknown utility intent: {intent}"
                return state
            
            response = model.generate_content(prompt)
            state["answer"] = response.text
            state["citations"] = []
            state["metadata"]["agent_type"] = "utility"
            state["metadata"]["utility_function"] = intent.lower()
            
        except Exception as e:
            state["error"] = f"Utility agent error: {str(e)}"
            state["answer"] = "I encountered an error processing your request."
        
        return state
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query."""
        result = genai.embed_content(
            model=self.embedding_model,
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']
    
    def _vector_search(
        self,
        query_embedding: List[float],
        chunks
    ) -> List[tuple]:
        """Perform vector similarity search."""
        results = []
        query_vec = np.array(query_embedding)
        
        for chunk in chunks:
            chunk_vec = np.array(chunk.embedding)
            # Cosine similarity
            similarity = np.dot(query_vec, chunk_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
            )
            results.append((chunk, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _bm25_search(self, query: str, chunks) -> List[tuple]:
        """Perform BM25 keyword search."""
        # Prepare corpus
        corpus = [chunk.text.lower().split() for chunk in chunks]
        
        # Initialize BM25
        bm25 = BM25Okapi(corpus)
        
        # Get scores
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        # Create results
        results = [(chunk, score) for chunk, score in zip(chunks, scores)]
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _combine_and_rerank(
        self,
        vector_results: List[tuple],
        bm25_results: List[tuple],
        query: str,
        alpha: float = 0.7
    ) -> List[tuple]:
        """
        Combine vector and BM25 results with reranking.
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            query: Original query
            alpha: Weight for vector search (1-alpha for BM25)
            
        Returns:
            Combined and reranked results
        """
        # Normalize scores
        def normalize_scores(results):
            if not results:
                return {}
            scores = [score for _, score in results]
            min_score = min(scores)
            max_score = max(scores)
            if max_score == min_score:
                return {chunk.id: 1.0 for chunk, _ in results}
            return {
                chunk.id: (score - min_score) / (max_score - min_score)
                for chunk, score in results
            }
        
        vector_scores = normalize_scores(vector_results)
        bm25_scores = normalize_scores(bm25_results)
        
        # Combine scores
        all_chunk_ids = set(vector_scores.keys()) | set(bm25_scores.keys())
        combined = {}
        
        for chunk_id in all_chunk_ids:
            vec_score = vector_scores.get(chunk_id, 0)
            bm25_score = bm25_scores.get(chunk_id, 0)
            combined[chunk_id] = alpha * vec_score + (1 - alpha) * bm25_score
        
        # Get chunks and sort by combined score
        chunk_dict = {chunk.id: chunk for chunk, _ in vector_results + bm25_results}
        final_results = [
            (chunk_dict[chunk_id], score)
            for chunk_id, score in combined.items()
        ]
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return final_results
