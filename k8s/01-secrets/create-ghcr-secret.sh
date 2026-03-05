#!/bin/bash
# Create Kubernetes Secret for GHCR Image Pull
# Usage: ./create-ghcr-secret.sh <github-username> <github-token> [namespace]

set -e

NAMESPACE=${3:-assocore}
GITHUB_USERNAME=${1}
GITHUB_TOKEN=${2}

if [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: Missing required arguments"
    echo ""
    echo "Usage: ./create-ghcr-secret.sh <github-username> <github-token> [namespace]"
    echo ""
    echo "Example:"
    echo "  ./create-ghcr-secret.sh fenrir42 ghp_xxxxxxxxxxxx assocore"
    echo ""
    echo "To create a token:"
    echo "  https://github.com/settings/tokens/new"
    echo "  Required scopes: read:packages"
    exit 1
fi

echo "Creating GHCR image pull secret..."
echo "Username: $GITHUB_USERNAME"
echo "Namespace: $NAMESPACE"
echo ""

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
kubectl create secret docker-registry ghcr-secret \
    --docker-server=ghcr.io \
    --docker-username="$GITHUB_USERNAME" \
    --docker-password="$GITHUB_TOKEN" \
    --docker-email="$GITHUB_USERNAME@users.noreply.github.com" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✓ GHCR secret created successfully!"
echo ""
echo "To use this secret in your deployments, add:"
echo "  imagePullSecrets:"
echo "    - name: ghcr-secret"
