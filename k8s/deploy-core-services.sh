#!/bin/bash
# Deploy complete Kubernetes cluster core services
# This script deploys Traefik, Watchtower, and creates necessary secrets

set -e

NAMESPACE="assocore"
GITHUB_USERNAME=${1:-""}
GITHUB_TOKEN=${2:-""}

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  AssoCORE Kubernetes Cluster Core Services Deployment         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to check if kubectl is installed
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "ERROR: kubectl is not installed"
        echo "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    local version=$(kubectl version --client -o json 2>/dev/null | grep -o '"gitVersion":"[^"]*"' | cut -d'"' -f4)
    echo "✓ kubectl found: ${version:-$(kubectl version --client 2>&1 | head -n1)}"
}

# Function to check cluster connectivity
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo "ERROR: Cannot connect to Kubernetes cluster"
        echo "Make sure your kubeconfig is properly configured"
        exit 1
    fi
    echo "✓ Connected to cluster: $(kubectl config current-context)"
    echo ""
}

# Main deployment
main() {
    check_kubectl
    check_cluster

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 1: Creating Namespace"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/00-namespace/namespace.yaml
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 2: Creating GHCR Image Pull Secret"
    echo "════════════════════════════════════════════════════════════════"
    if [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_TOKEN" ]; then
        echo "WARNING: GitHub credentials not provided"
        echo "Skipping GHCR secret creation"
        echo ""
        echo "To create the secret manually, run:"
        echo "  ./k8s/01-secrets/create-ghcr-secret.sh <username> <token>"
    else
        ./k8s/01-secrets/create-ghcr-secret.sh "$GITHUB_USERNAME" "$GITHUB_TOKEN" "$NAMESPACE"
    fi
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 3: Installing Traefik CRDs"
    echo "════════════════════════════════════════════════════════════════"
    ./k8s/02-traefik/install-crds.sh
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 4: Deploying Traefik Ingress Controller"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/02-traefik/traefik-rbac.yaml
    kubectl apply -f k8s/02-traefik/traefik-config.yaml
    kubectl apply -f k8s/02-traefik/traefik-deployment.yaml
    kubectl apply -f k8s/02-traefik/traefik-service.yaml
    
    echo ""
    echo "Waiting for Traefik to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/traefik -n "$NAMESPACE" || true
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 5: Deploying Traefik Dashboard"
    echo "════════════════════════════════════════════════════════════════"
    echo "WARNING: Default dashboard credentials are admin/admin"
    echo "Change the password in k8s/02-traefik/traefik-dashboard.yaml before production!"
    kubectl apply -f k8s/02-traefik/traefik-dashboard.yaml
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 6: Deploying Watchtower"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/03-watchtower/watchtower-deployment.yaml
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Deployment Summary"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    kubectl get all -n "$NAMESPACE"
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Next Steps"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "1. Get Traefik LoadBalancer IP:"
    echo "   kubectl get svc traefik -n $NAMESPACE"
    echo ""
    echo "2. Configure DNS to point to the LoadBalancer IP:"
    echo "   *.assocore.org -> <EXTERNAL-IP>"
    echo ""
    echo "3. Access Traefik Dashboard:"
    echo "   https://traefik.assocore.org/dashboard/"
    echo "   Username: admin"
    echo "   Password: admin (CHANGE THIS!)"
    echo ""
    echo "4. Update dashboard password:"
    echo "   htpasswd -nb admin new-password | base64"
    echo "   Update k8s/02-traefik/traefik-dashboard.yaml"
    echo ""
    echo "5. Deploy your applications:"
    echo "   kubectl apply -f k8s/apps/"
    echo ""
    echo "✓ Core services deployment complete!"
}

# Run main function
main "$@"
