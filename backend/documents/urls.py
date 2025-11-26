"""
URL configuration for documents app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from documents.views import DocumentViewSet, DocumentChunkViewSet

router = DefaultRouter()
router.register(r'', DocumentViewSet, basename='document')
router.register(r'chunks', DocumentChunkViewSet, basename='documentchunk')

urlpatterns = [
    path('', include(router.urls)),
]
