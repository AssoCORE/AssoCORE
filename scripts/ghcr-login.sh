#!/bin/bash
# Login to GitHub Container Registry (GHCR)
# Usage: ./scripts/ghcr-login.sh [USERNAME]

set -e

USERNAME=${1:-$USER}

echo "Logging into GitHub Container Registry (ghcr.io)..."
echo "Username: $USERNAME"
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN environment variable is not set"
    echo ""
    echo "To fix this:"
    echo "1. Create a Personal Access Token (PAT) at:"
    echo "   https://github.com/settings/tokens/new"
    echo ""
    echo "2. Select scopes: read:packages, write:packages, delete:packages"
    echo ""
    echo "3. Export the token:"
    echo "   export GITHUB_TOKEN=ghp_your_token_here"
    echo ""
    echo "4. Run this script again:"
    echo "   ./scripts/ghcr-login.sh $USERNAME"
    exit 1
fi

# Login to GHCR
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$USERNAME" --password-stdin

echo ""
echo "✓ Successfully logged in to ghcr.io"
echo ""
echo "You can now:"
echo "  - Push images: docker push ghcr.io/assocore/assocore/backend:latest"
echo "  - Pull images: docker pull ghcr.io/assocore/assocore/backend:latest"
