from django.db import models
import json


class TestQuery(models.Model):
    """Model for test queries used in evaluation"""

    query = models.TextField()
    expected_keywords = models.JSONField(
        default=list, help_text="List of keywords that should appear in the answer"
    )
    language = models.CharField(max_length=10, default="en")
    category = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.query[:50]}..."


class EvaluationRun(models.Model):
    """Model for evaluation runs"""

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_queries = models.IntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)
    results = models.JSONField(default=dict)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Evaluation Run {self.id} - {self.started_at}"


class QueryEvaluation(models.Model):
    """Model for individual query evaluation results"""

    run = models.ForeignKey(
        EvaluationRun, on_delete=models.CASCADE, related_name="evaluations"
    )
    test_query = models.ForeignKey(TestQuery, on_delete=models.CASCADE)
    answer = models.TextField()
    score = models.FloatField()
    citations_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for query {self.test_query.id} - Score: {self.score}"
