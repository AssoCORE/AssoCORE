#!/bin/bash
# Install k3s Multi-Node Cluster (High Availability)
# Usage: ./install-k3s-ha.sh <role> [master-ip] [token]
# Roles: master-init, master-join, worker

set -e

ROLE=${1:-""}
MASTER_IP=${2:-""}
TOKEN=${3:-""}
K3S_VERSION=${K3S_VERSION:-"v1.28.5+k3s1"}

usage() {
    echo "Usage: ./install-k3s-ha.sh <role> [master-ip] [token]"
    echo ""
    echo "Roles:"
    echo "  master-init          Initialize the first master node"
    echo "  master-join <ip> <token>   Join additional master nodes"
    echo "  worker <ip> <token>        Join as worker node"
    echo ""
    echo "Example:"
    echo "  # On first master:"
    echo "  ./install-k3s-ha.sh master-init"
    echo ""
    echo "  # On additional masters:"
    echo "  ./install-k3s-ha.sh master-join 192.168.1.10 K10xxx::server:xxx"
    echo ""
    echo "  # On workers:"
    echo "  ./install-k3s-ha.sh worker 192.168.1.10 K10xxx::server:xxx"
    exit 1
}

if [ -z "$ROLE" ]; then
    usage
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  k3s High Availability Installation                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

case "$ROLE" in
    master-init)
        echo "Installing FIRST MASTER node..."
        echo ""
        
        # Get public IP (adjust interface name as needed)
        PUBLIC_IP=$(ip -4 addr show $(ip route | grep default | awk '{print $5}' | head -n1) | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)
        
        curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" sh -s - server \
            --cluster-init \
            --write-kubeconfig-mode 644 \
            --disable traefik \
            --disable servicelb \
            --tls-san="${PUBLIC_IP}" \
            --tls-san="$(hostname)"
        
        echo ""
        echo "✓ First master node initialized!"
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "IMPORTANT: Save these values for other nodes:"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Master IP: ${PUBLIC_IP}"
        echo ""
        echo "Node Token (run on master node):"
        sudo cat /var/lib/rancher/k3s/server/node-token
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Setup kubeconfig:"
        mkdir -p $HOME/.kube
        sudo cat /etc/rancher/k3s/k3s.yaml > $HOME/.kube/config
        chmod 600 $HOME/.kube/config
        echo "export KUBECONFIG=$HOME/.kube/config" >> ~/.bashrc
        export KUBECONFIG=$HOME/.kube/config
        
        echo "✓ Kubeconfig configured"
        echo ""
        kubectl get nodes
        ;;
        
    master-join)
        if [ -z "$MASTER_IP" ] || [ -z "$TOKEN" ]; then
            echo "ERROR: Master IP and token required"
            usage
        fi
        
        echo "Joining as ADDITIONAL MASTER node..."
        echo "Master IP: $MASTER_IP"
        echo ""
        
        curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" sh -s - server \
            --server "https://${MASTER_IP}:6443" \
            --token "${TOKEN}" \
            --write-kubeconfig-mode 644 \
            --disable traefik \
            --disable servicelb
        
        echo ""
        echo "✓ Master node joined successfully!"
        ;;
        
    worker)
        if [ -z "$MASTER_IP" ] || [ -z "$TOKEN" ]; then
            echo "ERROR: Master IP and token required"
            usage
        fi
        
        echo "Joining as WORKER node..."
        echo "Master IP: $MASTER_IP"
        echo ""
        
        curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" \
            K3S_URL="https://${MASTER_IP}:6443" \
            K3S_TOKEN="${TOKEN}" sh -
        
        echo ""
        echo "✓ Worker node joined successfully!"
        ;;
        
    *)
        echo "ERROR: Unknown role: $ROLE"
        usage
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Installation Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ "$ROLE" = "master-init" ]; then
    echo "Next steps:"
    echo "1. Join additional master nodes (for HA)"
    echo "2. Join worker nodes"
    echo "3. Deploy AssoCORE: ./k8s/deploy-core-services.sh"
fi
