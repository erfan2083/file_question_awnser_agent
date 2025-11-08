"""Retriever Agent for finding relevant document chunks."""

from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from src.config.settings import settings
from src.models.schemas import AgentState, AgentType, RetrievalResult
from src.retrieval.hybrid_search import HybridRetriever


class RetrieverAgent:
    """Agent responsible for retrieving relevant document chunks."""

    def __init__(self, retriever: HybridRetriever = None):
        """
        Initialize Retriever Agent.

        Args:
            retriever: Hybrid retriever instance
        """
        self.retriever = retriever or HybridRetriever()

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key,
        )

        # Create tools
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()

    def _create_tools(self) -> List[Tool]:
        """
        Create tools for the retriever agent.

        Returns:
            List of tools
        """

        def retrieve_documents(query: str) -> str:
            """Retrieve relevant document chunks."""
            try:
                results = self.retriever.retrieve(query=query, use_reranking=True)
                if not results:
                    return "No relevant documents found."

                # Format results
                output_parts = []
                for i, result in enumerate(results, 1):
                    output_parts.append(
                        f"\n--- Result {i} (Score: {result.score:.3f}) ---\n"
                        f"Document ID: {result.chunk.document_id}\n"
                        f"Chunk ID: {result.chunk.chunk_id}\n"
                        f"Text: {result.chunk.text}\n"
                    )

                return "".join(output_parts)
            except Exception as e:
                logger.error(f"Error in retrieve_documents: {e}")
                return f"Error retrieving documents: {str(e)}"

        tools = [
            Tool(
                name="retrieve_documents",
                func=retrieve_documents,
                description=(
                    "Retrieves relevant document chunks based on a query. "
                    "Use this tool to find information from uploaded documents. "
                    "Input should be a clear search query."
                ),
            )
        ]

        return tools

    def _create_agent(self) -> AgentExecutor:
        """
        Create the retriever agent using ReAct pattern.

        Returns:
            AgentExecutor instance
        """
        prompt = PromptTemplate.from_template(
            """You are a document retrieval specialist. Your task is to find the most relevant 
information from documents to answer user queries.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to provide the retrieved documents
Final Answer: the retrieved documents and their relevance

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )

        agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
        )

        return agent_executor

    def execute(self, query: str, document_id: str = None) -> AgentState:
        """
        Execute the retriever agent.

        Args:
            query: User query
            document_id: Optional document ID to filter by

        Returns:
            AgentState with retrieved documents
        """
        logger.info(f"Retriever Agent executing query: {query}")

        try:
            # Directly use retriever for better control
            results = self.retriever.retrieve(
                query=query, document_id=document_id, use_reranking=True
            )

            # Format output
            output_data = {
                "query": query,
                "results": [
                    {
                        "chunk_id": r.chunk.chunk_id,
                        "document_id": r.chunk.document_id,
                        "text": r.chunk.text,
                        "score": r.score,
                        "metadata": r.chunk.metadata,
                    }
                    for r in results
                ],
                "num_results": len(results),
            }

            state = AgentState(
                agent_type=AgentType.RETRIEVER,
                input_data={"query": query, "document_id": document_id},
                output_data=output_data,
                metadata={"status": "success"},
            )

            logger.info(
                f"Retriever Agent completed successfully with {len(results)} results"
            )

            return state

        except Exception as e:
            logger.error(f"Error in Retriever Agent execution: {e}")
            return AgentState(
                agent_type=AgentType.RETRIEVER,
                input_data={"query": query, "document_id": document_id},
                output_data={},
                error=str(e),
                metadata={"status": "error"},
            )

    def get_retriever(self) -> HybridRetriever:
        """
        Get the underlying retriever.

        Returns:
            HybridRetriever instance
        """
        return self.retriever
