from .models import TestQuery, EvaluationRun, QueryEvaluation
from rag.retrieval import RetrievalService
from rag.agents import MultiAgentOrchestrator
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for running QA evaluations"""

    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.orchestrator = MultiAgentOrchestrator(self.retrieval_service)

    def run_evaluation(self):
        """Run evaluation on all active test queries"""

        # Get active test queries
        test_queries = TestQuery.objects.filter(is_active=True)

        if not test_queries.exists():
            logger.warning("No active test queries found")
            return None

        # Create evaluation run
        eval_run = EvaluationRun.objects.create(total_queries=test_queries.count())

        scores = []

        for test_query in test_queries:
            try:
                # Process query
                result = self.orchestrator.process_query(test_query.query)

                # Calculate score
                score = self._calculate_score(test_query, result["answer"])

                # Store evaluation
                QueryEvaluation.objects.create(
                    run=eval_run,
                    test_query=test_query,
                    answer=result["answer"],
                    score=score,
                    citations_count=len(result["citations"]),
                    metadata={
                        "citations": result["citations"],
                        "intent": result["intent"],
                    },
                )

                scores.append(score)

            except Exception as e:
                logger.error(f"Error evaluating query {test_query.id}: {str(e)}")
                QueryEvaluation.objects.create(
                    run=eval_run,
                    test_query=test_query,
                    answer="ERROR",
                    score=0.0,
                    citations_count=0,
                    metadata={"error": str(e)},
                )
                scores.append(0.0)

        # Update evaluation run
        eval_run.completed_at = timezone.now()
        eval_run.average_score = sum(scores) / len(scores) if scores else 0.0
        eval_run.results = {
            "scores": scores,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
        }
        eval_run.save()

        logger.info(
            f"Evaluation run {eval_run.id} completed with average score: {eval_run.average_score}"
        )

        return eval_run

    def _calculate_score(self, test_query: TestQuery, answer: str) -> float:
        """Calculate score for an answer based on expected keywords"""

        expected_keywords = test_query.expected_keywords
        if not expected_keywords:
            return 1.0  # If no keywords specified, assume success

        answer_lower = answer.lower()
        matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)

        score = matches / len(expected_keywords) if expected_keywords else 0.0
        return round(score, 2)
