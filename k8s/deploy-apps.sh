#!/bin/bash
# AssoCORE Application Deployment Script
# Deploy all application workloads to Kubernetes cluster

set -e

NAMESPACE="assocore"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AssoCORE Application Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' does not exist${NC}"
    echo -e "${YELLOW}Run 'kubectl apply -f k8s/00-namespace/' first${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating Application Secrets...${NC}"
# Check if .env file exists
if [ ! -f "k8s/.env" ]; then
    echo -e "${RED}Error: k8s/.env file not found!${NC}"
    echo ""
    echo -e "${YELLOW}Please create your secrets configuration:${NC}"
    echo "  1. Copy the template:"
    echo "     cp k8s/.env.example k8s/.env"
    echo ""
    echo "  2. Generate secure passwords:"
    echo "     openssl rand -base64 32"
    echo ""
    echo "  3. Edit k8s/.env and fill in all values"
    echo ""
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

# Create secrets from .env file
./k8s/01-secrets/create-app-secrets.sh
echo -e "${GREEN}✓ Secrets created${NC}"
echo ""

echo -e "${YELLOW}Step 2: Deploying Database (MariaDB)...${NC}"
kubectl apply -f k8s/07-database/mariadb-config.yaml
kubectl apply -f k8s/07-database/mariadb-statefulset.yaml
echo -e "${GREEN}✓ Database manifests applied${NC}"
echo "Waiting for MariaDB to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mariadb -n $NAMESPACE --timeout=300s
echo -e "${GREEN}✓ MariaDB is ready${NC}"
echo ""

echo -e "${YELLOW}Step 3: Deploying Cache (Redis)...${NC}"
kubectl apply -f k8s/08-redis/
echo -e "${GREEN}✓ Redis manifests applied${NC}"
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n $NAMESPACE --timeout=120s
echo -e "${GREEN}✓ Redis is ready${NC}"
echo ""

echo -e "${YELLOW}Step 4: Deploying Backend API...${NC}"
kubectl apply -f k8s/09-backend/backend-config.yaml
kubectl apply -f k8s/09-backend/backend-deployment.yaml
echo -e "${GREEN}✓ Backend manifests applied${NC}"
echo "Waiting for Backend to be ready..."
kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s
echo -e "${GREEN}✓ Backend is ready${NC}"
echo ""

echo -e "${YELLOW}Step 5: Deploying Frontend Web App...${NC}"

echo -e "${YELLOW}Step 5: Deploying Frontend Web App...${NC}"
kubectl apply -f k8s/10-frontend/
echo -e "${GREEN}✓ Frontend manifests applied${NC}"
echo "Waiting for Frontend to be ready..."
kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s
echo -e "${GREEN}✓ Frontend is ready${NC}"
echo ""

echo -e "${YELLOW}Step 6: Deploying NextCloud...${NC}"
kubectl apply -f k8s/11-nextcloud/nextcloud-config.yaml
kubectl apply -f k8s/11-nextcloud/nextcloud-statefulset.yaml
echo -e "${GREEN}✓ NextCloud manifests applied${NC}"
echo "Waiting for NextCloud to be ready (this may take a few minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=nextcloud -n $NAMESPACE --timeout=600s
echo -e "${GREEN}✓ NextCloud is ready${NC}"
echo ""

echo -e "${YELLOW}Step 7: Deploying Ingress Routes...${NC}"
kubectl apply -f k8s/12-ingress-apps/
echo -e "${GREEN}✓ Ingress routes applied${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show all pods
echo "Current pod status:"
kubectl get pods -n $NAMESPACE
echo ""

# Show all services
echo "Services:"
kubectl get svc -n $NAMESPACE
echo ""

# Show ingress routes
echo "Ingress routes:"
kubectl get ingressroute -n $NAMESPACE
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Access your services:${NC}"
echo ""
echo -e "  Frontend:  ${GREEN}http://assocore.localhost${NC}"
echo -e "  Backend:   ${GREEN}http://api.assocore.localhost${NC}"
echo -e "  NextCloud: ${GREEN}http://files.assocore.localhost${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} For local development, you may need to add these to /etc/hosts:"
echo ""
echo "  127.0.0.1 assocore.localhost"
echo "  127.0.0.1 api.assocore.localhost"
echo "  127.0.0.1 files.assocore.localhost"
echo ""
echo -e "${YELLOW}Your credentials are stored securely in Kubernetes secrets.${NC}"
echo -e "${YELLOW}To view NextCloud admin credentials:${NC}"
echo "  kubectl get secret nextcloud-secret -n assocore -o jsonpath='{.data.nextcloud-admin-user}' | base64 -d && echo"
echo "  kubectl get secret nextcloud-secret -n assocore -o jsonpath='{.data.nextcloud-admin-password}' | base64 -d && echo"
echo ""
echo -e "${RED}⚠️  SECURITY REMINDER:${NC}"
echo "  - Rotate your passwords regularly"
echo "  - Update credentials in k8s/.env and rerun: ./k8s/01-secrets/create-app-secrets.sh"
echo "  - Never commit k8s/.env to version control"
echo ""
echo -e "${YELLOW}Monitor your deployment:${NC}"
echo ""
echo "  kubectl get pods -n assocore -w"
echo "  kubectl logs -f -n assocore deployment/backend"
echo "  kubectl logs -f -n assocore deployment/frontend"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"
