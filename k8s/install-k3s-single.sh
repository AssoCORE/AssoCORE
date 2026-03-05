#!/bin/bash
# Install k3s Single Node Cluster
# Usage: ./install-k3s-single.sh [OPTIONS]

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  k3s Single Node Installation                                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
K3S_VERSION=${K3S_VERSION:-"v1.28.5+k3s1"}
INSTALL_DIR="$HOME/.kube"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "ERROR: Do not run this script as root"
    echo "k3s installation requires sudo, but the script should be run as a regular user"
    exit 1
fi

echo "Installing k3s ${K3S_VERSION}..."
echo ""

# Install k3s
echo "════════════════════════════════════════════════════════════════"
echo "Installing k3s server..."
echo "════════════════════════════════════════════════════════════════"

curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" sh -s - \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --disable servicelb

echo ""
echo "✓ k3s installed successfully"
echo ""

# Wait for k3s to be ready
echo "════════════════════════════════════════════════════════════════"
echo "Waiting for k3s to be ready..."
echo "════════════════════════════════════════════════════════════════"

sleep 5

for i in {1..30}; do
    if sudo k3s kubectl get nodes &>/dev/null; then
        echo "✓ k3s is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Setup kubeconfig
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Setting up kubeconfig..."
echo "════════════════════════════════════════════════════════════════"

mkdir -p "$INSTALL_DIR"
sudo cat /etc/rancher/k3s/k3s.yaml > "$INSTALL_DIR/config"
chmod 600 "$INSTALL_DIR/config"

echo "✓ Kubeconfig saved to: $INSTALL_DIR/config"
echo ""

# Set KUBECONFIG environment variable
export KUBECONFIG="$INSTALL_DIR/config"

# Add to shell profile
if ! grep -q "KUBECONFIG" ~/.bashrc 2>/dev/null; then
    echo "export KUBECONFIG=$INSTALL_DIR/config" >> ~/.bashrc
fi

if [ -f ~/.zshrc ] && ! grep -q "KUBECONFIG" ~/.zshrc; then
    echo "export KUBECONFIG=$INSTALL_DIR/config" >> ~/.zshrc
fi

# Verify installation
echo "════════════════════════════════════════════════════════════════"
echo "Verifying installation..."
echo "════════════════════════════════════════════════════════════════"

kubectl get nodes
echo ""
kubectl get pods -A

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Reload your shell or run:"
echo "   export KUBECONFIG=$INSTALL_DIR/config"
echo ""
echo "2. Deploy AssoCORE core services:"
echo "   cd /home/julien/delivery/EIP/AssoCORE"
echo "   ./k8s/deploy-core-services.sh fenrir42 \$GITHUB_TOKEN"
echo ""
echo "3. Check cluster status:"
echo "   kubectl cluster-info"
echo "   kubectl get nodes"
echo ""
echo "Useful commands:"
echo "  - View all pods: kubectl get pods -A"
echo "  - k3s logs: sudo journalctl -u k3s -f"
echo "  - Uninstall: /usr/local/bin/k3s-uninstall.sh"
echo ""
