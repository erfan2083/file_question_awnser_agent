from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TestQuery, EvaluationRun
from .serializers import (
    TestQuerySerializer,
    EvaluationRunSerializer,
)
from .services import EvaluationService
import logging

logger = logging.getLogger(__name__)


class TestQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for test queries"""

    queryset = TestQuery.objects.all()
    serializer_class = TestQuerySerializer


class EvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for evaluation runs"""

    queryset = EvaluationRun.objects.all()
    serializer_class = EvaluationRunSerializer

    @action(detail=False, methods=["post"], url_path="run")
    def run_evaluation(self, request):
        """Run a new evaluation"""
        try:
            evaluation_service = EvaluationService()
            eval_run = evaluation_service.run_evaluation()

            if not eval_run:
                return Response(
                    {"error": "No active test queries found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = EvaluationRunSerializer(eval_run)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error running evaluation: {str(e)}")
            return Response(
                {"error": "An error occurred running the evaluation"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
