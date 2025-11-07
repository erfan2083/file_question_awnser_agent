"""Reasoning Agent for synthesizing answers from retrieved evidence."""

from typing import Any, Dict, List

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from src.config.settings import settings
from src.models.schemas import AgentState, AgentType, Answer


class ReasoningAgent:
    """Agent responsible for reasoning and generating answers."""

    def __init__(self):
        """Initialize Reasoning Agent."""
        # Initialize LLM with higher temperature for more creative answers
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.max_output_tokens,
            google_api_key=settings.google_api_key,
        )

        # Create prompt template
        self.prompt = self._create_prompt()

        # Create LLM chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def _create_prompt(self) -> PromptTemplate:
        """
        Create prompt template for reasoning.

        Returns:
            PromptTemplate instance
        """
        template = """You are an intelligent reasoning assistant that synthesizes information from documents to answer questions accurately and comprehensively.

Your task is to:
1. Analyze the retrieved document chunks carefully
2. Identify the most relevant information for answering the question
3. Synthesize a clear, accurate, and well-structured answer
4. Cite specific document sources when making claims
5. If information is insufficient or unclear, acknowledge it honestly

Question: {question}

Retrieved Evidence:
{evidence}

Instructions:
- Provide a direct answer to the question based on the evidence
- Use chain-of-thought reasoning to work through complex questions
- Include citations to specific document chunks (use chunk IDs)
- If evidence is contradictory, acknowledge and explain the discrepancy
- If evidence is insufficient, say so clearly
- Keep the answer concise but complete
- Use natural, conversational language

Your Answer:"""

        return PromptTemplate(
            input_variables=["question", "evidence"], template=template
        )

    def execute(self, question: str, retrieval_results: List[Dict]) -> AgentState:
        """
        Execute the reasoning agent.

        Args:
            question: User question
            retrieval_results: List of retrieved document results

        Returns:
            AgentState with generated answer
        """
        logger.info(f"Reasoning Agent executing for question: {question}")

        try:
            # Format evidence from retrieval results
            evidence = self._format_evidence(retrieval_results)

            if not evidence.strip():
                # No evidence available
                answer_text = (
                    "I apologize, but I couldn't find relevant information in the documents "
                    "to answer your question. Could you please rephrase your question or "
                    "provide more context?"
                )
                confidence = 0.0
                sources = []
            else:
                # Generate answer using LLM
                response = self.chain.invoke({"question": question, "evidence": evidence})

                answer_text = response["text"].strip()
                confidence = self._estimate_confidence(answer_text, retrieval_results)
                sources = [r["chunk_id"] for r in retrieval_results]

            # Create Answer object
            answer = Answer(
                question=question,
                answer=answer_text,
                sources=sources,
                confidence=confidence,
                language="en",
            )

            # Create output state
            state = AgentState(
                agent_type=AgentType.REASONING,
                input_data={"question": question, "num_evidence_chunks": len(retrieval_results)},
                output_data={
                    "answer": answer_text,
                    "confidence": confidence,
                    "sources": sources,
                },
                metadata={"status": "success"},
            )

            logger.info("Reasoning Agent completed successfully")

            return state

        except Exception as e:
            logger.error(f"Error in Reasoning Agent execution: {e}")
            return AgentState(
                agent_type=AgentType.REASONING,
                input_data={"question": question},
                output_data={},
                error=str(e),
                metadata={"status": "error"},
            )

    def _format_evidence(self, retrieval_results: List[Dict]) -> str:
        """
        Format retrieval results as evidence text.

        Args:
            retrieval_results: List of retrieved results

        Returns:
            Formatted evidence string
        """
        if not retrieval_results:
            return ""

        evidence_parts = []
        for i, result in enumerate(retrieval_results, 1):
            chunk_id = result.get("chunk_id", f"chunk_{i}")
            text = result.get("text", "")
            score = result.get("score", 0.0)
            doc_id = result.get("document_id", "unknown")

            evidence_parts.append(
                f"[Document: {doc_id}, Chunk: {chunk_id}, Relevance: {score:.3f}]\n"
                f"{text}\n"
            )

        return "\n---\n".join(evidence_parts)

    def _estimate_confidence(
        self, answer: str, retrieval_results: List[Dict]
    ) -> float:
        """
        Estimate confidence score for the answer.

        Args:
            answer: Generated answer
            retrieval_results: Retrieved evidence

        Returns:
            Confidence score (0-1)
        """
        # Simple confidence estimation based on various factors
        confidence = 0.5  # Base confidence

        # Adjust based on number of sources
        if len(retrieval_results) > 0:
            confidence += min(len(retrieval_results) * 0.1, 0.3)

        # Adjust based on retrieval scores
        if retrieval_results:
            avg_score = sum(r.get("score", 0) for r in retrieval_results) / len(
                retrieval_results
            )
            confidence += avg_score * 0.2

        # Check for uncertainty markers in answer
        uncertainty_markers = [
            "i don't know",
            "unclear",
            "insufficient",
            "not sure",
            "may be",
            "might be",
            "possibly",
        ]
        answer_lower = answer.lower()
        if any(marker in answer_lower for marker in uncertainty_markers):
            confidence *= 0.7

        # Cap confidence at 1.0
        return min(confidence, 1.0)

    def answer_with_chain_of_thought(
        self, question: str, retrieval_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate answer with explicit chain-of-thought reasoning.

        Args:
            question: User question
            retrieval_results: List of retrieved results

        Returns:
            Dictionary with answer and reasoning steps
        """
        cot_template = """You are an intelligent reasoning assistant. Answer the question using step-by-step reasoning.

Question: {question}

Evidence:
{evidence}

Provide your reasoning in the following format:
1. Analysis: Analyze what the question is asking
2. Evidence Review: Summarize the key information from the evidence
3. Reasoning Steps: Show your step-by-step reasoning
4. Final Answer: Provide the final answer

Your detailed response:"""

        cot_prompt = PromptTemplate(
            input_variables=["question", "evidence"], template=cot_template
        )

        cot_chain = LLMChain(llm=self.llm, prompt=cot_prompt)

        evidence = self._format_evidence(retrieval_results)

        response = cot_chain.invoke({"question": question, "evidence": evidence})

        return {"reasoning": response["text"], "question": question}
