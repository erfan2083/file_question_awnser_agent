"""
Models for evaluation and testing.
"""

from django.db import models


class TestQuery(models.Model):
    """Model for storing test queries for evaluation."""
    
    query = models.TextField(help_text="Test question")
    expected_answer = models.TextField(
        blank=True,
        help_text="Expected answer or key phrases"
    )
    expected_keywords = models.JSONField(
        default=list,
        help_text="List of keywords that should appear in the answer"
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Query category (e.g., factual, summarization)"
    )
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"TestQuery {self.id}: {self.query[:50]}"


class EvaluationRun(models.Model):
    """Model for storing evaluation run results."""
    
    run_name = models.CharField(max_length=255, blank=True)
    total_queries = models.IntegerField(default=0)
    successful_queries = models.IntegerField(default=0)
    failed_queries = models.IntegerField(default=0)
    
    # Aggregate metrics
    average_score = models.FloatField(default=0.0)
    average_similarity = models.FloatField(default=0.0)
    average_response_time = models.FloatField(
        default=0.0,
        help_text="Average response time in seconds"
    )
    
    # Detailed results stored as JSON
    results = models.JSONField(default=list)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Evaluation {self.id} - {self.run_name or 'Unnamed'}"


class QueryResult(models.Model):
    """Model for storing individual query results within an evaluation run."""
    
    evaluation_run = models.ForeignKey(
        EvaluationRun,
        on_delete=models.CASCADE,
        related_name='query_results'
    )
    test_query = models.ForeignKey(
        TestQuery,
        on_delete=models.CASCADE,
        related_name='results'
    )
    
    generated_answer = models.TextField()
    score = models.FloatField(help_text="Score from 0 to 1")
    similarity_score = models.FloatField(default=0.0)
    response_time = models.FloatField(help_text="Response time in seconds")
    
    # Metadata: citations, keywords_found, etc.
    metadata = models.JSONField(default=dict)
    
    passed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['evaluation_run', 'id']
    
    def __str__(self):
        return f"Result for TestQuery {self.test_query.id} in Run {self.evaluation_run.id}"
