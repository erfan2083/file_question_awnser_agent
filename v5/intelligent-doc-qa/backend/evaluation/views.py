"""
Views for evaluation app.
"""

import time
from datetime import datetime
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from evaluation.models import TestQuery, EvaluationRun, QueryResult
from evaluation.serializers import (
    TestQuerySerializer,
    EvaluationRunSerializer,
    EvaluationRunListSerializer,
    QueryResultSerializer,
    RunEvaluationSerializer
)
from rag.services import RAGOrchestrator


class TestQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for test query management."""
    
    queryset = TestQuery.objects.all()
    serializer_class = TestQuerySerializer
    
    def get_queryset(self):
        """Filter by active status if requested."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset


class EvaluationRunViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for evaluation runs."""
    
    queryset = EvaluationRun.objects.all()
    serializer_class = EvaluationRunSerializer
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EvaluationRunListSerializer
        return EvaluationRunSerializer
    
    @action(detail=False, methods=['post'], url_path='run')
    def run_evaluation(self, request):
        """
        Run evaluation on test queries.
        
        Expected input:
        {
            "run_name": "Optional run name",
            "test_query_ids": [1, 2, 3]  // Optional, defaults to all active
        }
        """
        serializer = RunEvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        run_name = serializer.validated_data.get('run_name', f"Run {datetime.now()}")
        test_query_ids = serializer.validated_data.get('test_query_ids')
        
        # Get test queries
        if test_query_ids:
            test_queries = TestQuery.objects.filter(id__in=test_query_ids)
        else:
            test_queries = TestQuery.objects.filter(is_active=True)
        
        if not test_queries.exists():
            return Response(
                {'error': 'No test queries found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create evaluation run
        with transaction.atomic():
            eval_run = EvaluationRun.objects.create(
                run_name=run_name,
                total_queries=test_queries.count()
            )
            
            # Run evaluation
            orchestrator = RAGOrchestrator()
            results = []
            successful = 0
            failed = 0
            total_score = 0.0
            total_similarity = 0.0
            total_time = 0.0
            
            for test_query in test_queries:
                try:
                    # Time the query
                    start_time = time.time()
                    
                    # Process query
                    result = orchestrator.process_query(test_query.query)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # Calculate score
                    if result.get('error'):
                        score = 0.0
                        passed = False
                        error_msg = result['error']
                    else:
                        answer = result['answer']
                        score = self._calculate_score(
                            answer,
                            test_query.expected_answer,
                            test_query.expected_keywords
                        )
                        passed = score >= 0.5  # Threshold
                        error_msg = None
                    
                    # Calculate similarity (simple keyword overlap)
                    similarity = self._calculate_similarity(
                        result.get('answer', ''),
                        test_query.expected_answer
                    )
                    
                    # Create query result
                    query_result = QueryResult.objects.create(
                        evaluation_run=eval_run,
                        test_query=test_query,
                        generated_answer=result.get('answer', ''),
                        score=score,
                        similarity_score=similarity,
                        response_time=response_time,
                        metadata={
                            'citations': result.get('citations', []),
                            'metadata': result.get('metadata', {})
                        },
                        passed=passed,
                        error_message=error_msg
                    )
                    
                    if passed:
                        successful += 1
                    else:
                        failed += 1
                    
                    total_score += score
                    total_similarity += similarity
                    total_time += response_time
                    
                    results.append({
                        'test_query_id': test_query.id,
                        'score': score,
                        'passed': passed
                    })
                    
                except Exception as e:
                    failed += 1
                    QueryResult.objects.create(
                        evaluation_run=eval_run,
                        test_query=test_query,
                        generated_answer='',
                        score=0.0,
                        similarity_score=0.0,
                        response_time=0.0,
                        metadata={},
                        passed=False,
                        error_message=str(e)
                    )
            
            # Update evaluation run
            num_queries = test_queries.count()
            eval_run.successful_queries = successful
            eval_run.failed_queries = failed
            eval_run.average_score = total_score / num_queries if num_queries > 0 else 0
            eval_run.average_similarity = total_similarity / num_queries if num_queries > 0 else 0
            eval_run.average_response_time = total_time / num_queries if num_queries > 0 else 0
            eval_run.results = results
            eval_run.completed_at = datetime.now()
            eval_run.save()
        
        # Return results
        response_serializer = EvaluationRunSerializer(eval_run)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def _calculate_score(
        self,
        generated_answer: str,
        expected_answer: str,
        expected_keywords: list
    ) -> float:
        """
        Calculate score based on keyword presence and answer quality.
        
        Returns score between 0 and 1.
        """
        if not generated_answer:
            return 0.0
        
        score = 0.0
        generated_lower = generated_answer.lower()
        
        # Check for expected keywords
        if expected_keywords:
            keywords_found = sum(
                1 for keyword in expected_keywords
                if keyword.lower() in generated_lower
            )
            keyword_score = keywords_found / len(expected_keywords)
            score += keyword_score * 0.7  # 70% weight for keywords
        
        # Check similarity with expected answer
        if expected_answer:
            similarity = self._calculate_similarity(generated_answer, expected_answer)
            score += similarity * 0.3  # 30% weight for similarity
        
        return min(score, 1.0)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple word overlap similarity.
        
        Returns similarity score between 0 and 1.
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class QueryResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for query results."""
    
    queryset = QueryResult.objects.all()
    serializer_class = QueryResultSerializer
    
    def get_queryset(self):
        """Filter by evaluation run if provided."""
        queryset = super().get_queryset()
        eval_run_id = self.request.query_params.get('evaluation_run_id')
        
        if eval_run_id:
            queryset = queryset.filter(evaluation_run_id=eval_run_id)
        
        return queryset
