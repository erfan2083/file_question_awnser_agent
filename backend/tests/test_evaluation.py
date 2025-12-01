"""
Comprehensive tests for evaluation app.
Covers models, views, serializers, and evaluation logic.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from evaluation.models import TestQuery, EvaluationRun, QueryResult
from evaluation.serializers import (
    TestQuerySerializer,
    EvaluationRunSerializer,
    EvaluationRunListSerializer,
    QueryResultSerializer,
    RunEvaluationSerializer
)


# ============================================================
# Model Tests
# ============================================================

@pytest.mark.django_db
class TestTestQueryModel:
    """Tests for TestQuery model."""
    
    def test_create_test_query(self):
        """Test creating a test query."""
        query = TestQuery.objects.create(
            query="What is machine learning?",
            expected_answer="Machine learning is a subset of AI",
            expected_keywords=["machine", "learning", "AI"],
            category="factual",
            language="en"
        )
        
        assert query.id is not None
        assert query.query == "What is machine learning?"
        assert query.is_active is True
    
    def test_test_query_str_representation(self):
        """Test query string representation."""
        query = TestQuery.objects.create(
            query="A very long test query that should be truncated in the string representation",
            expected_answer="Expected answer"
        )
        
        assert "TestQuery" in str(query)
        assert str(query.id) in str(query)
    
    def test_test_query_with_persian(self):
        """Test query with Persian content."""
        query = TestQuery.objects.create(
            query="هوش مصنوعی چیست؟",
            expected_answer="هوش مصنوعی یک فناوری است",
            expected_keywords=["هوش", "مصنوعی"],
            language="fa"
        )
        
        assert query.language == "fa"
        assert "هوش" in query.expected_keywords
    
    def test_test_query_default_values(self):
        """Test default values for test query."""
        query = TestQuery.objects.create(
            query="Simple query"
        )
        
        assert query.expected_answer == ""
        assert query.expected_keywords == []
        assert query.category == ""
        assert query.language == "en"
        assert query.is_active is True
    
    def test_filter_active_queries(self):
        """Test filtering active queries."""
        TestQuery.objects.create(query="Active 1", is_active=True)
        TestQuery.objects.create(query="Active 2", is_active=True)
        TestQuery.objects.create(query="Inactive", is_active=False)
        
        active = TestQuery.objects.filter(is_active=True)
        assert active.count() == 2


@pytest.mark.django_db
class TestEvaluationRunModel:
    """Tests for EvaluationRun model."""
    
    def test_create_evaluation_run(self):
        """Test creating an evaluation run."""
        run = EvaluationRun.objects.create(
            run_name="Test Run 1",
            total_queries=10,
            successful_queries=8,
            failed_queries=2,
            average_score=0.75
        )
        
        assert run.id is not None
        assert run.run_name == "Test Run 1"
        assert run.average_score == 0.75
    
    def test_evaluation_run_str_representation(self):
        """Test run string representation."""
        run = EvaluationRun.objects.create(run_name="My Evaluation")
        
        assert "Evaluation" in str(run)
        assert "My Evaluation" in str(run)
    
    def test_evaluation_run_without_name(self):
        """Test run without name."""
        run = EvaluationRun.objects.create()
        
        assert "Unnamed" in str(run)
    
    def test_evaluation_run_ordering(self):
        """Test runs are ordered by started_at descending."""
        run1 = EvaluationRun.objects.create(run_name="Run 1")
        run2 = EvaluationRun.objects.create(run_name="Run 2")
        run3 = EvaluationRun.objects.create(run_name="Run 3")
        
        runs = list(EvaluationRun.objects.all())
        assert runs[0] == run3
        assert runs[1] == run2
        assert runs[2] == run1


@pytest.mark.django_db
class TestQueryResultModel:
    """Tests for QueryResult model."""
    
    def test_create_query_result(self, sample_evaluation_run, sample_test_query):
        """Test creating a query result."""
        result = QueryResult.objects.create(
            evaluation_run=sample_evaluation_run,
            test_query=sample_test_query,
            generated_answer="Machine learning is a subset of AI.",
            score=0.85,
            similarity_score=0.75,
            response_time=1.5,
            passed=True
        )
        
        assert result.id is not None
        assert result.score == 0.85
        assert result.passed is True
    
    def test_query_result_str_representation(self, sample_evaluation_run, sample_test_query):
        """Test result string representation."""
        result = QueryResult.objects.create(
            evaluation_run=sample_evaluation_run,
            test_query=sample_test_query,
            generated_answer="Answer",
            score=0.8,
            response_time=1.0
        )
        
        assert "TestQuery" in str(result)
        assert "Run" in str(result)
    
    def test_query_result_with_error(self, sample_evaluation_run, sample_test_query):
        """Test result with error message."""
        result = QueryResult.objects.create(
            evaluation_run=sample_evaluation_run,
            test_query=sample_test_query,
            generated_answer="",
            score=0.0,
            response_time=0.0,
            passed=False,
            error_message="Processing failed"
        )
        
        assert result.passed is False
        assert result.error_message == "Processing failed"


# ============================================================
# Serializer Tests
# ============================================================

@pytest.mark.django_db
class TestEvaluationSerializers:
    """Tests for evaluation serializers."""
    
    def test_test_query_serializer(self, sample_test_query):
        """Test TestQuerySerializer."""
        serializer = TestQuerySerializer(sample_test_query)
        data = serializer.data
        
        assert data['id'] == sample_test_query.id
        assert data['query'] == sample_test_query.query
        assert 'expected_keywords' in data
    
    def test_test_query_serializer_create(self):
        """Test creating a test query via serializer."""
        data = {
            'query': 'What is deep learning?',
            'expected_answer': 'Deep learning uses neural networks',
            'expected_keywords': ['deep', 'learning', 'neural'],
            'category': 'technical',
            'language': 'en'
        }
        serializer = TestQuerySerializer(data=data)
        
        assert serializer.is_valid()
        query = serializer.save()
        assert query.query == 'What is deep learning?'
    
    def test_evaluation_run_list_serializer(self, sample_evaluation_run):
        """Test EvaluationRunListSerializer."""
        serializer = EvaluationRunListSerializer(sample_evaluation_run)
        data = serializer.data
        
        assert data['id'] == sample_evaluation_run.id
        assert 'average_score' in data
        assert 'query_results' not in data  # List serializer doesn't include results
    
    def test_run_evaluation_serializer_valid(self):
        """Test RunEvaluationSerializer with valid data."""
        data = {
            'run_name': 'Test Run',
            'test_query_ids': [1, 2, 3]
        }
        serializer = RunEvaluationSerializer(data=data)
        
        assert serializer.is_valid()
    
    def test_run_evaluation_serializer_optional_fields(self):
        """Test RunEvaluationSerializer with optional fields."""
        data = {}  # All fields are optional
        serializer = RunEvaluationSerializer(data=data)
        
        assert serializer.is_valid()


# ============================================================
# View Tests
# ============================================================

@pytest.mark.django_db
class TestTestQueryViews:
    """Tests for test query views."""
    
    def test_list_test_queries(self, api_client, sample_test_query):
        """Test listing test queries."""
        response = api_client.get('/api/evaluation/test-queries/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_test_query(self, api_client):
        """Test creating a test query."""
        response = api_client.post(
            '/api/evaluation/test-queries/',
            {
                'query': 'What is NLP?',
                'expected_answer': 'NLP is Natural Language Processing',
                'expected_keywords': ['NLP', 'natural', 'language'],
                'category': 'technical'
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['query'] == 'What is NLP?'
    
    def test_retrieve_test_query(self, api_client, sample_test_query):
        """Test retrieving a test query."""
        response = api_client.get(
            f'/api/evaluation/test-queries/{sample_test_query.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_test_query(self, api_client, sample_test_query):
        """Test updating a test query."""
        response = api_client.patch(
            f'/api/evaluation/test-queries/{sample_test_query.id}/',
            {'is_active': False},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        sample_test_query.refresh_from_db()
        assert sample_test_query.is_active is False
    
    def test_delete_test_query(self, api_client, sample_test_query):
        """Test deleting a test query."""
        query_id = sample_test_query.id
        response = api_client.delete(
            f'/api/evaluation/test-queries/{query_id}/'
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TestQuery.objects.filter(id=query_id).exists()
    
    def test_filter_active_queries(self, api_client):
        """Test filtering active queries."""
        TestQuery.objects.create(query="Active", is_active=True)
        TestQuery.objects.create(query="Inactive", is_active=False)
        
        response = api_client.get('/api/evaluation/test-queries/?is_active=true')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestEvaluationRunViews:
    """Tests for evaluation run views."""
    
    def test_list_evaluation_runs(self, api_client, sample_evaluation_run):
        """Test listing evaluation runs."""
        response = api_client.get('/api/evaluation/runs/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_retrieve_evaluation_run(self, api_client, sample_evaluation_run):
        """Test retrieving an evaluation run."""
        response = api_client.get(
            f'/api/evaluation/runs/{sample_evaluation_run.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['run_name'] == sample_evaluation_run.run_name
    
    @patch('evaluation.views.RAGOrchestrator')
    def test_run_evaluation(self, mock_rag, api_client, sample_test_query):
        """Test running an evaluation."""
        mock_rag.return_value.process_query.return_value = {
            'answer': 'Machine learning is a subset of AI that enables systems to learn.',
            'citations': [],
            'metadata': {'intent': 'RAG_QUERY'},
            'error': ''
        }
        
        response = api_client.post(
            '/api/evaluation/runs/run/',
            {
                'run_name': 'Test Evaluation',
                'test_query_ids': [sample_test_query.id]
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['run_name'] == 'Test Evaluation'
        assert data['total_queries'] == 1
    
    @patch('evaluation.views.RAGOrchestrator')
    def test_run_evaluation_all_active(self, mock_rag, api_client, sample_test_query):
        """Test running evaluation on all active queries."""
        mock_rag.return_value.process_query.return_value = {
            'answer': 'Test answer',
            'citations': [],
            'metadata': {},
            'error': ''
        }
        
        response = api_client.post(
            '/api/evaluation/runs/run/',
            {'run_name': 'All Active Queries'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_run_evaluation_no_queries(self, api_client):
        """Test running evaluation with no queries."""
        # Deactivate all queries
        TestQuery.objects.all().update(is_active=False)
        
        response = api_client.post(
            '/api/evaluation/runs/run/',
            {'run_name': 'Empty Run'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestQueryResultViews:
    """Tests for query result views."""
    
    def test_list_query_results(self, api_client, sample_evaluation_run, sample_test_query):
        """Test listing query results."""
        QueryResult.objects.create(
            evaluation_run=sample_evaluation_run,
            test_query=sample_test_query,
            generated_answer="Answer",
            score=0.8,
            response_time=1.0
        )
        
        response = api_client.get('/api/evaluation/results/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_results_by_run(self, api_client, sample_evaluation_run, sample_test_query):
        """Test filtering results by evaluation run."""
        QueryResult.objects.create(
            evaluation_run=sample_evaluation_run,
            test_query=sample_test_query,
            generated_answer="Answer",
            score=0.8,
            response_time=1.0
        )
        
        response = api_client.get(
            f'/api/evaluation/results/?evaluation_run_id={sample_evaluation_run.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# Scoring Logic Tests
# ============================================================

@pytest.mark.django_db
class TestScoringLogic:
    """Tests for evaluation scoring logic."""
    
    def test_calculate_score_with_keywords(self):
        """Test score calculation with keyword matching."""
        from evaluation.views import EvaluationRunViewSet
        
        viewset = EvaluationRunViewSet()
        
        score = viewset._calculate_score(
            "Machine learning is a subset of artificial intelligence.",
            "Machine learning is AI",
            ["machine", "learning", "AI"]
        )
        
        assert score > 0.5  # Should find keywords
    
    def test_calculate_score_no_match(self):
        """Test score calculation with no matches."""
        from evaluation.views import EvaluationRunViewSet
        
        viewset = EvaluationRunViewSet()
        
        score = viewset._calculate_score(
            "The weather is nice today.",
            "Machine learning is AI",
            ["machine", "learning", "AI"]
        )
        
        assert score < 0.5  # Should not find keywords
    
    def test_calculate_score_empty_answer(self):
        """Test score calculation with empty answer."""
        from evaluation.views import EvaluationRunViewSet
        
        viewset = EvaluationRunViewSet()
        
        score = viewset._calculate_score(
            "",
            "Expected answer",
            ["keyword"]
        )
        
        assert score == 0.0
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        from evaluation.views import EvaluationRunViewSet
        
        viewset = EvaluationRunViewSet()
        
        # Same text
        similarity = viewset._calculate_similarity(
            "machine learning is great",
            "machine learning is great"
        )
        assert similarity == 1.0
        
        # Different text
        similarity = viewset._calculate_similarity(
            "the cat sat on the mat",
            "dogs are running outside"
        )
        assert similarity < 0.5
    
    def test_calculate_similarity_empty(self):
        """Test similarity with empty text."""
        from evaluation.views import EvaluationRunViewSet
        
        viewset = EvaluationRunViewSet()
        
        similarity = viewset._calculate_similarity("", "text")
        assert similarity == 0.0
        
        similarity = viewset._calculate_similarity("text", "")
        assert similarity == 0.0
