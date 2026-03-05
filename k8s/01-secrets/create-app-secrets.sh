#!/bin/bash
# Create Kubernetes secrets from environment variables
# This script reads credentials from .env file and creates Kubernetes secrets

set -e

NAMESPACE="assocore"
ENV_FILE="k8s/.env"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and fill in your credentials:${NC}"
    echo "  cp k8s/.env.example k8s/.env"
    echo "  nano k8s/.env"
    exit 1
fi

# Load environment variables from .env file
echo -e "${YELLOW}Loading credentials from $ENV_FILE...${NC}"
set -a
source "$ENV_FILE"
set +a

# Validate required variables
REQUIRED_VARS=(
    "MARIADB_ROOT_PASSWORD"
    "MARIADB_DATABASE"
    "MARIADB_USER"
    "MARIADB_PASSWORD"
    "NEXTCLOUD_ADMIN_USER"
    "NEXTCLOUD_ADMIN_PASSWORD"
    "GRAFANA_ADMIN_USER"
    "GRAFANA_ADMIN_PASSWORD"
    "TRAEFIK_DASHBOARD_USER"
    "TRAEFIK_DASHBOARD_PASSWORD"
)

MISSING_VARS=()
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "  - $VAR"
    done
    echo ""
    echo -e "${YELLOW}Please edit $ENV_FILE and set all required values.${NC}"
    echo -e "${YELLOW}Generate secure passwords with:${NC}"
    echo "  openssl rand -base64 32"
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' does not exist${NC}"
    echo -e "${YELLOW}Create it with: kubectl create namespace $NAMESPACE${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating Kubernetes Secrets${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create MariaDB secret
echo -e "${YELLOW}Creating MariaDB secret...${NC}"
kubectl create secret generic mariadb-secret \
    --from-literal=root-password="$MARIADB_ROOT_PASSWORD" \
    --from-literal=database="$MARIADB_DATABASE" \
    --from-literal=user="$MARIADB_USER" \
    --from-literal=password="$MARIADB_PASSWORD" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ MariaDB secret created/updated${NC}"
echo ""

# Create Backend database secret
echo -e "${YELLOW}Creating Backend database secret...${NC}"
DATABASE_URL="mysql+aiomysql://${MARIADB_USER}:${MARIADB_PASSWORD}@mariadb.assocore.svc.cluster.local:3306/${MARIADB_DATABASE}"

kubectl create secret generic backend-db-secret \
    --from-literal=database-url="$DATABASE_URL" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Backend database secret created/updated${NC}"
echo ""

# Create NextCloud secret
echo -e "${YELLOW}Creating NextCloud secret...${NC}"
kubectl create secret generic nextcloud-secret \
    --from-literal=mysql-database="$MARIADB_DATABASE" \
    --from-literal=mysql-user="$MARIADB_USER" \
    --from-literal=mysql-password="$MARIADB_PASSWORD" \
    --from-literal=nextcloud-admin-user="$NEXTCLOUD_ADMIN_USER" \
    --from-literal=nextcloud-admin-password="$NEXTCLOUD_ADMIN_PASSWORD" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ NextCloud secret created/updated${NC}"
echo ""

# Create Grafana secret
echo -e "${YELLOW}Creating Grafana secret...${NC}"
kubectl create secret generic grafana-admin \
    --from-literal=admin-user="$GRAFANA_ADMIN_USER" \
    --from-literal=admin-password="$GRAFANA_ADMIN_PASSWORD" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Grafana secret created/updated${NC}"
echo ""

# Create Traefik Dashboard Auth secret
echo -e "${YELLOW}Creating Traefik Dashboard Auth secret...${NC}"

# Check if htpasswd is available (preferred method)
if command -v htpasswd &> /dev/null; then
    # Generate htpasswd format
    HTPASSWD_ENTRY=$(htpasswd -nb "$TRAEFIK_DASHBOARD_USER" "$TRAEFIK_DASHBOARD_PASSWORD")
else
    # Fallback to openssl
    echo -e "${YELLOW}Note: htpasswd not found, using openssl (install apache2-utils for better security)${NC}"
    PASSWORD_HASH=$(openssl passwd -apr1 "$TRAEFIK_DASHBOARD_PASSWORD")
    HTPASSWD_ENTRY="${TRAEFIK_DASHBOARD_USER}:${PASSWORD_HASH}"
fi

kubectl create secret generic traefik-dashboard-auth-secret \
    --from-literal=users="$HTPASSWD_ENTRY" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Traefik Dashboard Auth secret created/updated${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Secrets Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Verify secrets:${NC}"
echo "  kubectl get secrets -n $NAMESPACE"
echo ""
echo -e "${YELLOW}View secret details (base64 encoded):${NC}"
echo "  kubectl get secret mariadb-secret -n $NAMESPACE -o yaml"
echo ""
echo -e "${RED}⚠️  SECURITY REMINDER:${NC}"
echo "  - Never commit .env file to version control"
echo "  - Store production credentials securely"
echo "  - Rotate passwords regularly"
echo "  - Use sealed-secrets or external secret managers in production"
echo ""
