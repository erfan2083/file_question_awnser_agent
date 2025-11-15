from rest_framework import serializers
from .models import TestQuery, EvaluationRun, QueryEvaluation


class TestQuerySerializer(serializers.ModelSerializer):
    """Serializer for test queries"""

    class Meta:
        model = TestQuery
        fields = [
            "id",
            "query",
            "expected_keywords",
            "language",
            "category",
            "is_active",
            "created_at",
        ]


class QueryEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for query evaluations"""

    query_text = serializers.CharField(source="test_query.query", read_only=True)

    class Meta:
        model = QueryEvaluation
        fields = [
            "id",
            "query_text",
            "answer",
            "score",
            "citations_count",
            "metadata",
            "created_at",
        ]


class EvaluationRunSerializer(serializers.ModelSerializer):
    """Serializer for evaluation runs"""

    evaluations = QueryEvaluationSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationRun
        fields = [
            "id",
            "started_at",
            "completed_at",
            "total_queries",
            "average_score",
            "results",
            "evaluations",
        ]
