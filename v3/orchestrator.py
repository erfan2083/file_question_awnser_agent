"""Multi-agent orchestrator using LangGraph for workflow coordination."""

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.reasoning_agent import ReasoningAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.utility_agent import UtilityAgent
from src.models.schemas import Answer, UtilityTask


class OrchestratorState(TypedDict):
    """State for the orchestrator workflow."""

    question: str
    document_id: str | None
    retrieval_results: List[Dict[str, Any]]
    answer: str | None
    utility_task: str | None
    utility_result: str | None
    error: str | None
    metadata: Dict[str, Any]


class MultiAgentOrchestrator:
    """Orchestrates multiple agents using LangGraph workflows."""

    def __init__(
        self,
        retriever_agent: RetrieverAgent = None,
        reasoning_agent: ReasoningAgent = None,
        utility_agent: UtilityAgent = None,
    ):
        """
        Initialize multi-agent orchestrator.

        Args:
            retriever_agent: Retriever agent instance
            reasoning_agent: Reasoning agent instance
            utility_agent: Utility agent instance
        """
        self.retriever_agent = retriever_agent or RetrieverAgent()
        self.reasoning_agent = reasoning_agent or ReasoningAgent()
        self.utility_agent = utility_agent or UtilityAgent()

        # Create workflow graph
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """
        Create LangGraph workflow for agent orchestration.

        Returns:
            StateGraph workflow
        """
        # Define workflow
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("utility", self._utility_node)

        # Define edges
        workflow.set_entry_point("retrieve")

        # After retrieval, check if we should go to utility or reasoning
        workflow.add_conditional_edges(
            "retrieve",
            self._should_use_utility,
            {
                "utility": "utility",
                "reason": "reason",
            },
        )

        # After utility, go to reasoning
        workflow.add_edge("utility", "reason")

        # After reasoning, end
        workflow.add_edge("reason", END)

        return workflow.compile()

    def _retrieve_node(self, state: OrchestratorState) -> OrchestratorState:
        """
        Retrieval node - retrieve relevant documents.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing retrieval node")

        try:
            retriever_state = self.retriever_agent.execute(
                query=state["question"], document_id=state.get("document_id")
            )

            if retriever_state.error:
                state["error"] = retriever_state.error
                state["retrieval_results"] = []
            else:
                state["retrieval_results"] = retriever_state.output_data.get(
                    "results", []
                )

            state["metadata"]["retrieval_status"] = "completed"

        except Exception as e:
            logger.error(f"Error in retrieval node: {e}")
            state["error"] = str(e)
            state["retrieval_results"] = []

        return state

    def _reason_node(self, state: OrchestratorState) -> OrchestratorState:
        """
        Reasoning node - generate answer from retrieved documents.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing reasoning node")

        try:
            reasoning_state = self.reasoning_agent.execute(
                question=state["question"],
                retrieval_results=state["retrieval_results"],
            )

            if reasoning_state.error:
                state["error"] = reasoning_state.error
                state["answer"] = "Error generating answer"
            else:
                state["answer"] = reasoning_state.output_data.get("answer", "")

            state["metadata"]["reasoning_status"] = "completed"

        except Exception as e:
            logger.error(f"Error in reasoning node: {e}")
            state["error"] = str(e)
            state["answer"] = "Error generating answer"

        return state

    def _utility_node(self, state: OrchestratorState) -> OrchestratorState:
        """
        Utility node - perform utility tasks if needed.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing utility node")

        try:
            utility_task = state.get("utility_task")
            if not utility_task:
                return state

            # Convert task string to UtilityTask enum
            task_enum = UtilityTask(utility_task)

            # Get text from retrieval results
            text = "\n\n".join(
                [r.get("text", "") for r in state["retrieval_results"]]
            )

            # Execute utility task
            utility_state = self.utility_agent.execute(
                task=task_enum, text=text, target_language=state["metadata"].get("target_language", "es")
            )

            if utility_state.error:
                state["error"] = utility_state.error
            else:
                state["utility_result"] = utility_state.output_data.get("result", "")

            state["metadata"]["utility_status"] = "completed"

        except Exception as e:
            logger.error(f"Error in utility node: {e}")
            state["error"] = str(e)

        return state

    def _should_use_utility(self, state: OrchestratorState) -> str:
        """
        Decide whether to use utility agent.

        Args:
            state: Current workflow state

        Returns:
            Next node name
        """
        if state.get("utility_task"):
            return "utility"
        return "reason"

    def answer_question(
        self, question: str, document_id: str = None, use_chain_of_thought: bool = False
    ) -> Answer:
        """
        Answer a question using the multi-agent system.

        Args:
            question: User question
            document_id: Optional document ID to filter by
            use_chain_of_thought: Whether to use chain-of-thought reasoning

        Returns:
            Answer object
        """
        logger.info(f"Orchestrator answering question: {question}")

        # Initialize state
        initial_state: OrchestratorState = {
            "question": question,
            "document_id": document_id,
            "retrieval_results": [],
            "answer": None,
            "utility_task": None,
            "utility_result": None,
            "error": None,
            "metadata": {},
        }

        # Execute workflow
        final_state = self.workflow.invoke(initial_state)

        # Extract results
        answer_text = final_state.get("answer", "Unable to generate answer")
        sources = [
            r.get("chunk_id", "") for r in final_state.get("retrieval_results", [])
        ]

        # Create Answer object
        answer = Answer(
            question=question,
            answer=answer_text,
            sources=sources,
            confidence=0.8,  # Can be improved with better confidence estimation
            language="en",
        )

        logger.info("Orchestrator completed successfully")

        return answer

    def perform_utility_task(
        self,
        task: UtilityTask,
        text: str = None,
        question: str = None,
        **kwargs
    ) -> str:
        """
        Perform a utility task.

        Args:
            task: Utility task to perform
            text: Optional text input
            question: Optional question (will retrieve documents if provided)
            **kwargs: Additional task-specific parameters

        Returns:
            Task result
        """
        logger.info(f"Orchestrator performing utility task: {task.value}")

        if question and not text:
            # Retrieve documents first
            initial_state: OrchestratorState = {
                "question": question,
                "document_id": kwargs.get("document_id"),
                "retrieval_results": [],
                "answer": None,
                "utility_task": task.value,
                "utility_result": None,
                "error": None,
                "metadata": kwargs,
            }

            final_state = self.workflow.invoke(initial_state)
            return final_state.get("utility_result", "")

        else:
            # Direct utility task
            utility_state = self.utility_agent.execute(task=task, text=text, **kwargs)
            return utility_state.output_data.get("result", "")

    def get_agents(self) -> tuple:
        """
        Get all agent instances.

        Returns:
            Tuple of (retriever_agent, reasoning_agent, utility_agent)
        """
        return self.retriever_agent, self.reasoning_agent, self.utility_agent
