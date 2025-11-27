# Intelligent Document QA - Backend

Django backend for the Intelligent Document Question Answering System with Hexagonal Architecture.

## Features

- Document processing and storage
- RAG (Retrieval-Augmented Generation) with LangChain
- Google Gemini AI integration
- Vector search with pgvector
- RESTful API with Django REST Framework

## Architecture

This project follows Hexagonal (Ports & Adapters) Architecture:
- **Domain**: Core business logic
- **Application**: Use cases and application services
- **Infrastructure**: External adapters (database, AI services, etc.)
- **API**: HTTP interface layer

## Technology Stack

- Python 3.11+
- Django 5.0+
- PostgreSQL with pgvector
- LangChain & LangGraph
- Google Gemini AI
