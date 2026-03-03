#!/usr/bin/env bash
set -e

echo "🚀 AssoCORE Backend Setup"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
  echo "📝 Creating .env from .env.example..."
  cp .env.example .env
  echo "⚠️  Please edit .env with your configuration"
fi

# Setup uv environment
echo "📦 Setting up Python environment with uv..."
uv sync

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
  echo "🐳 Docker service is not running. Attempting to start Docker..."
  sudo systemctl start docker

  TIME_START=$(date +%s)
  echo "⏳ Waiting for Docker to start..."
  until systemctl is-active --quiet docker; do
    TIME_NOW=$(date +%s)
    TIME_ELAPSED=$((TIME_NOW - TIME_START))
    echo -ne "  ${TIME_ELAPSED}s\r"
    sleep 2

    if [ $TIME_ELAPSED -gt 60 ]; then
      echo -e "\n❌ Timeout waiting for Docker. Please check Docker service manually."
      exit 1
    fi
  done
  echo -e "\n✅ Docker service started successfully."
fi

# Deploy stack
echo "🚢 Starting Nextcloud + MariaDB + Redis + API..."
docker compose up -d --build

echo "⏳ Waiting for Database to be ready..."
until docker exec $(docker compose ps -q db) mariadb-admin ping -h"localhost" --silent 2>/dev/null; do
  sleep 2
done

echo "⏳ Waiting for Nextcloud to be ready..."
sleep 5

# Check if Nextcloud is installed
if docker exec -u www-data $(docker compose ps -q nextcloud) php occ status 2>/dev/null | grep -q "installed: true"; then
  echo "✅ Nextcloud is already installed."

  echo "🔧 Configuring trusted domains..."
  docker exec -u www-data $(docker compose ps -q nextcloud) php occ config:system:set trusted_domains 0 --value=localhost:8081 || true
  docker exec -u www-data $(docker compose ps -q nextcloud) php occ config:system:set trusted_domains 1 --value=nextcloud || true

  echo "📱 Installing recommended apps..."
  docker exec -u www-data $(docker compose ps -q nextcloud) php occ app:install calendar || true
  docker exec -u www-data $(docker compose ps -q nextcloud) php occ app:install contacts || true
  docker exec -u www-data $(docker compose ps -q nextcloud) php occ app:install notes || true
else
  echo "⚠️  Nextcloud is ready but not yet installed."
  echo "   Please complete setup at http://localhost:8081"
  echo "   Use credentials from .env file"
fi

# Final output
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Nextcloud:  http://localhost:8081"
echo "🔌 API:        http://localhost:8000"
echo "📚 API Docs:   http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
