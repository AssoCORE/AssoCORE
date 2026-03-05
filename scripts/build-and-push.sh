#!/bin/bash
# Build, tag, and push Docker images to GHCR
# Usage: ./scripts/build-and-push.sh [TAG]

set -e

TAG=${1:-latest}
REPO="ghcr.io/assocore/assocore"

echo "Building and pushing Docker images..."
echo "Tag: $TAG"
echo "Repository: $REPO"
echo ""

# Check if logged in
if ! docker info | grep -q "ghcr.io"; then
    echo "Not logged in to GHCR. Running login script..."
    ./scripts/ghcr-login.sh
fi

# Backend
echo "📦 Building backend..."
docker build -f docker/backend.Dockerfile -t "$REPO/backend:$TAG" .
echo "⬆️  Pushing backend..."
docker push "$REPO/backend:$TAG"
echo "✓ Backend pushed"
echo ""

# Frontend
echo "📦 Building frontend..."
docker build -f docker/frontend.Dockerfile -t "$REPO/frontend:$TAG" .
echo "⬆️  Pushing frontend..."
docker push "$REPO/frontend:$TAG"
echo "✓ Frontend pushed"
echo ""

# Mobile (optional - only build, don't push as it's just for APK generation)
read -p "Build mobile image? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Building mobile..."
    docker build -f docker/mobile.Dockerfile -t "$REPO/mobile:$TAG" .
    echo "⬆️  Pushing mobile..."
    docker push "$REPO/mobile:$TAG"
    echo "✓ Mobile pushed"
fi

echo ""
echo "✓ All images built and pushed successfully!"
echo ""
echo "Images:"
echo "  - $REPO/backend:$TAG"
echo "  - $REPO/frontend:$TAG"
echo ""
echo "To deploy:"
echo "  docker compose -f docker-compose.prod.yml pull"
echo "  docker compose -f docker-compose.prod.yml up -d"
