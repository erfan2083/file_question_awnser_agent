"""
Serializers for evaluation app.
"""

from rest_framework import serializers
from evaluation.models import TestQuery, EvaluationRun, QueryResult


class TestQuerySerializer(serializers.ModelSerializer):
    """Serializer for test queries."""
    
    class Meta:
        model = TestQuery
        fields = [
            'id', 'query', 'expected_answer', 'expected_keywords',
            'category', 'language', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QueryResultSerializer(serializers.ModelSerializer):
    """Serializer for query results."""
    
    test_query = TestQuerySerializer(read_only=True)
    
    class Meta:
        model = QueryResult
        fields = [
            'id', 'test_query', 'generated_answer', 'score',
            'similarity_score', 'response_time', 'metadata',
            'passed', 'error_message', 'created_at'
        ]
        read_only_fields = fields


class EvaluationRunSerializer(serializers.ModelSerializer):
    """Serializer for evaluation runs."""
    
    query_results = QueryResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = EvaluationRun
        fields = [
            'id', 'run_name', 'total_queries', 'successful_queries',
            'failed_queries', 'average_score', 'average_similarity',
            'average_response_time', 'results', 'started_at',
            'completed_at', 'query_results'
        ]
        read_only_fields = fields


class EvaluationRunListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing evaluation runs."""
    
    class Meta:
        model = EvaluationRun
        fields = [
            'id', 'run_name', 'total_queries', 'successful_queries',
            'failed_queries', 'average_score', 'average_similarity',
            'average_response_time', 'started_at', 'completed_at'
        ]
        read_only_fields = fields


class RunEvaluationSerializer(serializers.Serializer):
    """Serializer for running evaluation."""
    
    run_name = serializers.CharField(max_length=255, required=False)
    test_query_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Optional list of test query IDs to run. If not provided, runs all active queries."
    )
