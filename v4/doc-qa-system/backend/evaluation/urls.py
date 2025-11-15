from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestQueryViewSet, EvaluationViewSet

router = DefaultRouter()
router.register(r"queries", TestQueryViewSet, basename="testquery")
router.register(r"results", EvaluationViewSet, basename="evaluation")

urlpatterns = [
    path("", include(router.urls)),
]
