#!/bin/bash
# Build, tag, and push Docker images to GHCR
# Usage: ./scripts/build-and-push.sh [TAG]

set -e

TAG=${1:-latest}
REPO="ghcr.io/assocore/assocore"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Building and Pushing Docker Images to GHCR${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Tag: $TAG"
echo "Repository: $REPO"
echo ""

# Check if logged in
if ! docker info | grep -q "ghcr.io"; then
    echo -e "${YELLOW}Not logged in to GHCR. Running login script...${NC}"
    ./scripts/ghcr-login.sh
    echo ""
fi

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Backend
echo -e "${BLUE}📦 Building backend...${NC}"
docker build \
    -f docker/backend.Dockerfile \
    --target production \
    -t "$REPO/backend:$TAG" \
    .
echo -e "${BLUE}⬆️  Pushing backend...${NC}"
docker push "$REPO/backend:$TAG"
echo -e "${GREEN}✓ Backend pushed${NC}"
echo ""

# Frontend
echo -e "${BLUE}📦 Building frontend...${NC}"
docker build \
    -f docker/frontend.Dockerfile \
    --target production \
    -t "$REPO/frontend:$TAG" \
    .
echo -e "${BLUE}⬆️  Pushing frontend...${NC}"
docker push "$REPO/frontend:$TAG"
echo -e "${GREEN}✓ Frontend pushed${NC}"
echo ""

# Mobile (optional - only build, don't push as it's just for APK generation)
if [ "$2" = "--with-mobile" ]; then
    echo -e "${BLUE}📦 Building mobile...${NC}"
    docker build \
        -f docker/mobile.Dockerfile \
        --target production \
        -t "$REPO/mobile:$TAG" \
        .
    echo -e "${BLUE}⬆️  Pushing mobile...${NC}"
    docker push "$REPO/mobile:$TAG"
    echo -e "${GREEN}✓ Mobile pushed${NC}"
    echo ""
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All images built and pushed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Images tagged as:"
echo "  - $REPO/backend:$TAG"
echo "  - $REPO/frontend:$TAG"
if [ "$2" = "--with-mobile" ]; then
    echo "  - $REPO/mobile:$TAG"
fi
echo ""
echo "Images:"
echo "  - $REPO/backend:$TAG"
echo "  - $REPO/frontend:$TAG"
echo ""
echo "To deploy:"
echo "  docker compose -f docker-compose.prod.yml pull"
echo "  docker compose -f docker-compose.prod.yml up -d"
