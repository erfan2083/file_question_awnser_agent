"""
Management command to initialize sample test queries
"""
from django.core.management.base import BaseCommand
from evaluation.models import TestQuery


class Command(BaseCommand):
    help = "Initialize sample test queries for evaluation"

    def handle(self, *args, **kwargs):
        test_queries = [
            {
                "query": "What is the main topic of the document?",
                "expected_keywords": ["topic", "main", "document"],
                "language": "en",
                "category": "general",
            },
            {
                "query": "Summarize the key findings",
                "expected_keywords": ["summary", "findings", "key"],
                "language": "en",
                "category": "summarization",
            },
            {
                "query": "این سند در مورد چیست؟",
                "expected_keywords": ["سند", "مورد"],
                "language": "fa",
                "category": "general",
            },
            {
                "query": "What are the main recommendations?",
                "expected_keywords": ["recommendations", "main"],
                "language": "en",
                "category": "specific",
            },
            {
                "query": "List the key action items",
                "expected_keywords": ["action", "items", "list"],
                "language": "en",
                "category": "checklist",
            },
        ]

        for query_data in test_queries:
            TestQuery.objects.get_or_create(
                query=query_data["query"],
                defaults={
                    "expected_keywords": query_data["expected_keywords"],
                    "language": query_data["language"],
                    "category": query_data["category"],
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully initialized {len(test_queries)} test queries"
            )
        )
