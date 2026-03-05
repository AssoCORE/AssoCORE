#!/bin/bash
# Install k3d (k3s in Docker) for WSL
# Perfect for development in WSL/Docker Desktop

set -e

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
echo "Creating k3d cluster 'assocore'..."
echo "════════════════════════════════════════════════════════════════"

k3d cluster create assocore \
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
k3d kubeconfig get assocore > ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config

# Add to shell profile
if ! grep -q "KUBECONFIG" ~/.bashrc 2>/dev/null; then
    echo "export KUBECONFIG=~/.kube/config" >> ~/.bashrc
fi

if [ -f ~/.zshrc ] && ! grep -q "KUBECONFIG" ~/.zshrc; then
    echo "export KUBECONFIG=~/.kube/config" >> ~/.zshrc
fi

echo "✓ Kubeconfig configured"
echo ""

# Verify installation
echo "════════════════════════════════════════════════════════════════"
echo "Verifying cluster..."
echo "════════════════════════════════════════════════════════════════"

kubectl get nodes
echo ""
kubectl cluster-info

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Cluster: assocore"
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
echo "  - Stop cluster: k3d cluster stop assocore"
echo "  - Start cluster: k3d cluster start assocore"
echo "  - Delete cluster: k3d cluster delete assocore"
echo "  - View logs: k3d cluster logs assocore"
echo ""
