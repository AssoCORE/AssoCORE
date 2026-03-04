#!/usr/bin/env bash
set -e

echo "🛑 Stopping AssoCORE Backend Stack..."
docker compose down -v --remove-orphans

echo "✅ Shutdown complete."
