"""
URL configuration for evaluation app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from evaluation.views import (
    TestQueryViewSet,
    EvaluationRunViewSet,
    QueryResultViewSet
)

router = DefaultRouter()
router.register(r'test-queries', TestQueryViewSet, basename='testquery')
router.register(r'runs', EvaluationRunViewSet, basename='evaluationrun')
router.register(r'results', QueryResultViewSet, basename='queryresult')

urlpatterns = [
    path('', include(router.urls)),
]
