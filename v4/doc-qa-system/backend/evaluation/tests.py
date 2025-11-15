import pytest
from evaluation.models import TestQuery, EvaluationRun, QueryEvaluation
from evaluation.services import EvaluationService
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestQueryModel:
    """Tests for TestQuery model"""

    def test_create_test_query(self):
        query = TestQuery.objects.create(
            query="Test question?",
            expected_keywords=["test", "question"],
            language="en",
        )
        assert query.query == "Test question?"
        assert query.is_active is True


@pytest.mark.django_db
class TestEvaluationRun:
    """Tests for EvaluationRun model"""

    def test_create_evaluation_run(self):
        run = EvaluationRun.objects.create(total_queries=5, average_score=0.75)
        assert run.total_queries == 5
        assert run.average_score == 0.75


@pytest.mark.django_db
class TestEvaluationService:
    """Tests for EvaluationService"""

    def test_calculate_score(self, test_query):
        service = EvaluationService()
        answer = "The main topic is testing"
        score = service._calculate_score(test_query, answer)
        assert 0.0 <= score <= 1.0
        assert score > 0  # Should find at least one keyword

    def test_calculate_score_no_keywords(self):
        service = EvaluationService()
        query = TestQuery(query="Test", expected_keywords=[])
        score = service._calculate_score(query, "Any answer")
        assert score == 1.0


@pytest.mark.django_db
class TestEvaluationAPI:
    """Tests for Evaluation API endpoints"""

    def test_list_test_queries(self, test_query):
        client = APIClient()
        response = client.get("/api/evaluation/queries/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_list_evaluation_results(self, evaluation_run):
        client = APIClient()
        response = client.get("/api/evaluation/results/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_run_evaluation(self, test_query, sample_document, sample_chunk):
        client = APIClient()
        response = client.post("/api/evaluation/results/run/")
        assert response.status_code == 201
        assert "average_score" in response.data
