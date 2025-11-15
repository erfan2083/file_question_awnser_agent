#!/bin/bash

# Quick Start Script for Intelligent Document QA System

echo "🚀 Starting Intelligent Document QA System Setup..."
echo ""

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env file"
    echo "⚠️  Please edit backend/.env and add your GOOGLE_API_KEY"
    echo ""
    read -p "Press Enter after you've added your Google API key to backend/.env..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "📦 Running database migrations..."
docker-compose exec -T backend python manage.py migrate

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Admin Panel: http://localhost:8000/admin"
echo ""
echo "📝 To create an admin user, run:"
echo "   docker-compose exec backend python manage.py createsuperuser"
echo ""
echo "🛑 To stop the application:"
echo "   docker-compose down"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
