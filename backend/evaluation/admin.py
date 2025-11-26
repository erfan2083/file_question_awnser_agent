from django.contrib import admin
from evaluation.models import TestQuery, EvaluationRun, QueryResult


@admin.register(TestQuery)
class TestQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'query', 'category', 'language', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'language']
    search_fields = ['query']
    readonly_fields = ['created_at']


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'run_name', 'total_queries', 'average_score', 'started_at']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(QueryResult)
class QueryResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'evaluation_run', 'test_query', 'score', 'passed']
    list_filter = ['passed', 'created_at']
    readonly_fields = ['created_at']
