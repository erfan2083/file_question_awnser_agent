#!/bin/bash

# Setup script for the Document Q&A System

set -e

echo "=================================================="
echo "Document Q&A System - Setup Script"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your GOOGLE_API_KEY"
    echo "You can get an API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Check if GOOGLE_API_KEY is set
source .env
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key-here" ]; then
    echo "Error: GOOGLE_API_KEY is not set in .env file"
    exit 1
fi

echo "Building Docker containers..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for database to be ready..."
sleep 10

echo ""
echo "Running database migrations..."
docker-compose exec -T backend python manage.py migrate

echo ""
echo "Creating superuser (for Django admin)..."
docker-compose exec backend python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

echo ""
echo "Initializing sample test queries..."
docker-compose exec -T backend python manage.py init_test_queries

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo "=================================================="
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000/api"
echo "  Django Admin: http://localhost:8000/admin"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""
echo "To run tests:"
echo "  docker-compose exec backend pytest"
echo ""
