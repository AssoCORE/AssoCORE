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

# Function to check if app secrets exist
check_app_secrets() {
    echo "════════════════════════════════════════════════════════════════"
    echo "Checking Application Secrets"
    echo "════════════════════════════════════════════════════════════════"
    
    local missing_secrets=()
    
    # Check for required secrets
    if ! kubectl get secret mariadb-secret -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("mariadb-secret")
    fi
    if ! kubectl get secret grafana-admin -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("grafana-admin")
    fi
    if ! kubectl get secret traefik-dashboard-auth-secret -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("traefik-dashboard-auth-secret")
    fi
    
    if [ ${#missing_secrets[@]} -gt 0 ]; then
        echo "⚠️  WARNING: Missing required secrets:"
        for secret in "${missing_secrets[@]}"; do
            echo "  - $secret"
        done
        echo ""
        echo "Create secrets before deploying:"
        echo "  1. Copy k8s/.env.example to k8s/.env"
        echo "  2. Edit k8s/.env and set all required credentials"
        echo "  3. Run: ./k8s/01-secrets/create-app-secrets.sh"
        echo ""
        echo "Press Enter to continue anyway, or Ctrl+C to abort..."
        read
    else
        echo "✓ All required application secrets exist"
    fi
    echo ""
}

# Main deployment
main() {
    check_kubectl
    check_cluster
    check_app_secrets

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
    echo "Note: Watchtower is disabled by default (replicas: 0)"
    echo "      It requires Docker, but k3s/k3d uses containerd"
    echo "      Enable only if you have Docker runtime: kubectl scale deployment/watchtower --replicas=1 -n assocore"
    kubectl apply -f k8s/03-watchtower/watchtower-deployment.yaml
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 7: Deploying Prometheus (Monitoring)"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/04-prometheus/prometheus-rbac.yaml
    kubectl apply -f k8s/04-prometheus/prometheus-config.yaml
    kubectl apply -f k8s/04-prometheus/prometheus-deployment.yaml
    kubectl apply -f k8s/04-prometheus/prometheus-service.yaml
    echo ""
    echo "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=available --timeout=180s deployment/prometheus -n "$NAMESPACE" || true
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 8: Deploying Grafana (Visualization)"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/05-grafana/grafana-config.yaml
    kubectl apply -f k8s/05-grafana/grafana-dashboards.yaml
    kubectl apply -f k8s/05-grafana/grafana-deployment.yaml
    kubectl apply -f k8s/05-grafana/grafana-service.yaml
    echo ""
    echo "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=available --timeout=180s deployment/grafana -n "$NAMESPACE" || true
    echo ""

    echo "════════════════════════════════════════════════════════════════"
    echo "Step 9: Deploying Ingress Routes"
    echo "════════════════════════════════════════════════════════════════"
    kubectl apply -f k8s/06-ingress/observability-ingress.yaml
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
    echo "1. Access Traefik Dashboard:"
    echo "   kubectl port-forward -n $NAMESPACE svc/traefik-dashboard 9000:9000"
    echo "   http://localhost:9000/dashboard/"
    echo "   Username: admin | Password: admin (CHANGE THIS!)"
    echo ""
    echo "2. Access Prometheus (Monitoring):"
    echo "   kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
    echo "   http://localhost:9090"
    echo "   OR: http://prometheus.localhost (if using k3d)"
    echo ""
    echo "3. Access Grafana (Dashboards):"
    echo "   kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
    echo "   http://localhost:3000"
    echo "   OR: http://grafana.localhost (if using k3d)"
    echo "   Credentials: Set via k8s/.env (GRAFANA_ADMIN_USER / GRAFANA_ADMIN_PASSWORD)"
    echo ""
    echo "4. Rotate credentials:"
    echo "   - Update k8s/.env with new passwords"
    echo "   - Run: ./k8s/01-secrets/create-app-secrets.sh"
    echo "   - Restart affected pods: kubectl rollout restart deployment/<name> -n $NAMESPACE"
    echo ""
    echo "5. Deploy your applications:"
    echo "   kubectl apply -f k8s/apps/"
    echo ""
    echo "✓ Core services deployment complete!"
    echo "  ✓ Namespace: $NAMESPACE"
    echo "  ✓ Traefik Ingress Controller"
    echo "  ✓ Watchtower Auto-updater (disabled by default)"
    echo "  ✓ Prometheus Monitoring"
    echo "  ✓ Grafana Visualization"
}

# Run main function
main "$@"
