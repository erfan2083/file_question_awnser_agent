from django.contrib import admin
from .models import TestQuery, EvaluationRun, QueryEvaluation


@admin.register(TestQuery)
class TestQueryAdmin(admin.ModelAdmin):
    list_display = ["query", "language", "category", "is_active", "created_at"]
    list_filter = ["language", "category", "is_active"]
    search_fields = ["query"]


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ["id", "started_at", "completed_at", "total_queries", "average_score"]
    readonly_fields = ["started_at", "completed_at"]


@admin.register(QueryEvaluation)
class QueryEvaluationAdmin(admin.ModelAdmin):
    list_display = ["id", "run", "test_query", "score", "citations_count", "created_at"]
    list_filter = ["run"]
    readonly_fields = ["created_at"]
