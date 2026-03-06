#!/bin/bash
# Install k3d (k3s in Docker) for WSL
# Perfect for development in WSL/Docker Desktop
#
# Usage: ./install-k3d.sh [cluster-name]
# Default cluster name: assocore

set -e

# Get cluster name from parameter or use default
CLUSTER_NAME="${1:-assocore}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  k3d Installation (k3s in Docker for WSL)                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker ps &>/dev/null; then
    echo "ERROR: Docker is not running"
    echo ""
    echo "Please ensure Docker Desktop is running on Windows"
    echo "You can install from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Install k3d
echo "════════════════════════════════════════════════════════════════"
echo "Installing k3d..."
echo "════════════════════════════════════════════════════════════════"

curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

echo ""
echo "✓ k3d installed successfully"
echo ""

# Create cluster
echo "════════════════════════════════════════════════════════════════"
echo "Creating k3d cluster '$CLUSTER_NAME'..."
echo "═══════════════════════════════════════════════════════════════="

k3d cluster create "$CLUSTER_NAME" \
    --api-port 6443 \
    --servers 1 \
    --agents 2 \
    --port "80:80@loadbalancer" \
    --port "443:443@loadbalancer" \
    --k3s-arg "--disable=traefik@server:0" \
    --k3s-arg "--disable=servicelb@server:0"

echo ""
echo "✓ Cluster created successfully"
echo ""

# Setup kubeconfig
echo "════════════════════════════════════════════════════════════════"
echo "Configuring kubectl..."
echo "════════════════════════════════════════════════════════════════"

mkdir -p ~/.kube
k3d kubeconfig get "$CLUSTER_NAME" > ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config

# Add to shell profile (with error handling)
echo "Adding KUBECONFIG to shell configuration..."

# Try to add to .bashrc if it exists
if [ -f ~/.bashrc ]; then
    if ! grep -q "KUBECONFIG" ~/.bashrc 2>/dev/null; then
        if [ -w ~/.bashrc ]; then
            echo "export KUBECONFIG=~/.kube/config" >> ~/.bashrc && echo "  ✓ Added to ~/.bashrc"
        else
            echo "  ⚠️  Cannot write to ~/.bashrc (permission denied)"
        fi
    else
        echo "  ✓ Already in ~/.bashrc"
    fi
fi

# Try to add to .zshrc if it exists
if [ -f ~/.zshrc ]; then
    if ! grep -q "KUBECONFIG" ~/.zshrc 2>/dev/null; then
        if [ -w ~/.zshrc ]; then
            echo "export KUBECONFIG=~/.kube/config" >> ~/.zshrc && echo "  ✓ Added to ~/.zshrc"
        else
            echo "  ⚠️  Cannot write to ~/.zshrc (permission denied - you may need to add it manually)"
        fi
    else
        echo "  ✓ Already in ~/.zshrc"
    fi
fi

echo ""
echo "ℹ️  If KUBECONFIG was not added automatically, run this command:"
echo "   echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc"
echo "   source ~/.zshrc"
echo ""

echo "✓ Kubeconfig configured"
echo ""

# Verify installation
echo "════════════════════════════════════════════════════════════════"
echo "Verifying cluster..."
echo "════════════════════════════════════════════════════════════════"

if kubectl get nodes 2>/dev/null; then
    echo "✓ kubectl connected to cluster successfully"
    echo ""
    kubectl cluster-info
else
    echo "⚠️  kubectl could not connect to cluster"
    echo ""
    echo "This usually means KUBECONFIG is not set in your current session."
    echo ""
    echo "Run this command now:"
    echo "  export KUBECONFIG=~/.kube/config"
    echo ""
    echo "Then verify:"
    echo "  kubectl get nodes"
    echo ""
    echo "See docs/KUBECTL_CONNECTION_FIX.md for more help"
    echo ""
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Cluster: $CLUSTER_NAME"
echo "Servers: 1"
echo "Agents: 2"
echo ""
echo "Next steps:"
echo ""
echo "1. Deploy AssoCORE core services:"
echo "   ./k8s/deploy-core-services.sh fenrir42 \$GITHUB_TOKEN"
echo ""
echo "2. Access services on localhost:"
echo "   - HTTP: http://localhost"
echo "   - HTTPS: https://localhost"
echo ""
echo "Useful commands:"
echo "  - List clusters: k3d cluster list"
echo "  - Stop cluster: k3d cluster stop $CLUSTER_NAME"
echo "  - Start cluster: k3d cluster start $CLUSTER_NAME"
echo "  - Delete cluster: k3d cluster delete $CLUSTER_NAME"
echo "  - View logs: k3d cluster logs $CLUSTER_NAME"
echo ""
