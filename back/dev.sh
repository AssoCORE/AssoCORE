#!/usr/bin/env bash
set -e

echo "🚀 Starting AssoCORE Backend Development Server"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example"
    cp .env.example .env
fi

# Check if Docker services are running
if ! docker compose ps | grep -q "Up"; then
    echo "⚠️  Docker services not running. Starting them..."
    docker compose up -d db redis nextcloud --remove-orphans
    echo "⏳ Waiting for services to be ready..."
    sleep 5
else
    # Ensure api is not running
    docker compose stop api 2>/dev/null || true
fi

echo "🔧 Starting API with hot reload in Docker..."
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

docker compose -f docker-compose.yml -f docker-compose.dev.yml up api-dev
