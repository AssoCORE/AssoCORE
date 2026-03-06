#!/bin/bash
# AssoCORE Complete Automated Deployment Script
# This script handles everything from cluster creation to full application deployment
#
# Usage: ./k8s/deploy-all.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="assocore"

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${GREEN}AssoCORE Complete Deployment Script${CYAN}               ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  This script will guide you through the entire setup       ║${NC}"
echo -e "${CYAN}║  from cluster creation to running applications             ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================================
# FRESH START OPTION
# ==============================================================================

# Temporary function for yes/no (full one defined later)
prompt_yes_no_simple() {
    local prompt="$1"
    local default="$2"
    local response

    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi

    while true; do
        read -p "$prompt" response
        response=${response,,}

        if [ -z "$response" ]; then
            response=$default
        fi

        case $response in
            y|yes) return 0 ;;
            n|no) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

echo -e "${YELLOW}⚠️  Fresh Start Option${NC}"
echo ""
echo "Do you want to perform a fresh start?"
echo "This will:"
echo "  - Delete existing k3d/k3s clusters"
echo "  - Stop and remove project-related Docker containers"
echo "  - Remove existing configuration files (.env, .deployment-info)"
echo "  - Clean up Kubernetes resources"
echo ""
echo -e "${RED}WARNING: This will delete all existing data!${NC}"
echo ""

if prompt_yes_no_simple "Perform fresh start?" "n"; then
    echo ""
    echo -e "${BLUE}Performing fresh start cleanup...${NC}"
    echo ""

    # Clean up k3d clusters
    if command -v k3d >/dev/null 2>&1; then
        echo -e "${YELLOW}Checking for k3d clusters...${NC}"
        K3D_CLUSTERS=$(k3d cluster list -o json 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

        if [ -n "$K3D_CLUSTERS" ]; then
            echo "Found k3d clusters:"
            echo "$K3D_CLUSTERS"
            echo ""

            for cluster in $K3D_CLUSTERS; do
                # Check if cluster name contains 'assocore' or ask for confirmation
                if [[ "$cluster" == *"assocore"* ]]; then
                    echo -e "${BLUE}Deleting k3d cluster: $cluster${NC}"
                    k3d cluster delete "$cluster" 2>/dev/null || true
                else
                    if prompt_yes_no_simple "Delete k3d cluster '$cluster'?" "n"; then
                        echo -e "${BLUE}Deleting k3d cluster: $cluster${NC}"
                        k3d cluster delete "$cluster" 2>/dev/null || true
                    fi
                fi
            done
            echo -e "${GREEN}✓ k3d clusters cleaned up${NC}"
        else
            echo -e "${GREEN}✓ No k3d clusters found${NC}"
        fi
    fi

    # Clean up k3s
    if command -v k3s >/dev/null 2>&1; then
        echo ""
        echo -e "${YELLOW}k3s is installed${NC}"

        if prompt_yes_no_simple "Uninstall k3s?" "n"; then
            echo -e "${BLUE}Uninstalling k3s...${NC}"
            if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
                sudo /usr/local/bin/k3s-uninstall.sh
                echo -e "${GREEN}✓ k3s uninstalled${NC}"
            else
                echo -e "${YELLOW}⊘ k3s uninstall script not found${NC}"
            fi
        else
            # Just delete the namespace if k3s exists
            if kubectl get namespace $NAMESPACE &>/dev/null 2>&1; then
                echo -e "${BLUE}Deleting Kubernetes namespace: $NAMESPACE${NC}"
                kubectl delete namespace $NAMESPACE --timeout=60s 2>/dev/null || true
                echo -e "${GREEN}✓ Namespace deleted${NC}"
            fi
        fi
    fi

    # Clean up Docker containers
    if command -v docker >/dev/null 2>&1; then
        echo ""
        echo -e "${YELLOW}Checking for project Docker containers...${NC}"

        # Stop and remove containers with 'assocore' in name
        ASSOCORE_CONTAINERS=$(docker ps -a --filter "name=assocore" --format "{{.Names}}" 2>/dev/null || echo "")

        if [ -n "$ASSOCORE_CONTAINERS" ]; then
            echo "Found AssoCORE containers:"
            echo "$ASSOCORE_CONTAINERS"
            echo ""
            echo -e "${BLUE}Stopping and removing containers...${NC}"

            for container in $ASSOCORE_CONTAINERS; do
                docker stop "$container" 2>/dev/null || true
                docker rm "$container" 2>/dev/null || true
            done

            echo -e "${GREEN}✓ Docker containers cleaned up${NC}"
        else
            echo -e "${GREEN}✓ No AssoCORE containers found${NC}"
        fi
    fi

    # Clean up configuration files
    echo ""
    echo -e "${YELLOW}Cleaning up configuration files...${NC}"

    if [ -f "$SCRIPT_DIR/.env" ]; then
        # Backup before deleting
        BACKUP_FILE="$SCRIPT_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$SCRIPT_DIR/.env" "$BACKUP_FILE"
        rm "$SCRIPT_DIR/.env"
        echo -e "${GREEN}✓ .env removed (backup: $BACKUP_FILE)${NC}"
    fi

    if [ -f "$SCRIPT_DIR/.deployment-info" ]; then
        rm "$SCRIPT_DIR/.deployment-info"
        echo -e "${GREEN}✓ .deployment-info removed${NC}"
    fi

    # Clean up kubeconfig
    if [ -f "$HOME/.kube/config" ]; then
        if prompt_yes_no_simple "Remove kubectl config (~/.kube/config)?" "n"; then
            BACKUP_FILE="$HOME/.kube/config.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$HOME/.kube/config" "$BACKUP_FILE"
            rm "$HOME/.kube/config"
            echo -e "${GREEN}✓ kubectl config removed (backup: $BACKUP_FILE)${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}✓ Fresh start cleanup complete!${NC}"
    echo ""
    echo -e "${CYAN}Starting fresh deployment...${NC}"
    echo ""

    # Small pause to let user see the cleanup results
    sleep 2
else
    echo -e "${GREEN}✓ Skipping fresh start - using existing resources${NC}"
    echo ""
fi

# ==============================================================================
# FUNCTIONS
# ==============================================================================

# Function to prompt for yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local response

    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi

    while true; do
        read -p "$prompt" response
        response=${response,,} # to lowercase

        if [ -z "$response" ]; then
            response=$default
        fi

        case $response in
            y|yes) return 0 ;;
            n|no) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to prompt for password with option to generate
prompt_password() {
    local var_name="$1"
    local description="$2"
    local generated_pwd=$(generate_password)

    echo -e "${YELLOW}$description${NC}"
    echo -e "${CYAN}Generated password: ${GREEN}$generated_pwd${NC}"

    if prompt_yes_no "Use this generated password?" "y"; then
        eval "$var_name='$generated_pwd'"
    else
        read -p "Enter custom password: " -s custom_pwd
        echo ""
        eval "$var_name='$custom_pwd'"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}Checking prerequisites...${NC}"
echo ""

# Check for required tools
MISSING_TOOLS=()

if ! command_exists kubectl; then
    MISSING_TOOLS+=("kubectl")
fi

if ! command_exists openssl; then
    MISSING_TOOLS+=("openssl")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required tools:${NC}"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo -e "  - $tool"
    done
    echo ""
    echo "Please install them and try again."
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# ==============================================================================
# STEP 1: Cluster Selection
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 1: Cluster Setup${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

CLUSTER_TYPE=""
SKIP_CLUSTER_INSTALL=false

# Check if a cluster already exists
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓ Kubernetes cluster already accessible${NC}"
    kubectl cluster-info
    echo ""

    if prompt_yes_no "Use this existing cluster?" "y"; then
        SKIP_CLUSTER_INSTALL=true
        CLUSTER_TYPE="existing"
    else
        echo -e "${YELLOW}Will set up a new cluster${NC}"
    fi
fi

if [ "$SKIP_CLUSTER_INSTALL" = false ]; then
    echo "Which Kubernetes distribution do you want to use?"
    echo ""
    echo -e "  ${GREEN}1)${NC} k3d (Kubernetes in Docker) - Recommended for development"
    echo "     - Lightweight, fast startup"
    echo "     - Requires Docker"
    echo "     - Easy cleanup"
    echo ""
    echo -e "  ${GREEN}2)${NC} k3s (Lightweight Kubernetes) - For production/bare-metal"
    echo "     - Runs directly on host"
    echo "     - Production-ready"
    echo "     - Requires sudo access"
    echo ""

    while true; do
        read -p "Enter choice [1-2]: " cluster_choice
        case $cluster_choice in
            1)
                CLUSTER_TYPE="k3d"
                break
                ;;
            2)
                CLUSTER_TYPE="k3s"
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1 or 2.${NC}"
                ;;
        esac
    done
fi

# Install cluster if needed
if [ "$SKIP_CLUSTER_INSTALL" = false ]; then
    echo ""
    echo -e "${BLUE}Installing $CLUSTER_TYPE cluster...${NC}"

    if [ "$CLUSTER_TYPE" = "k3d" ]; then
        # Check if Docker is running
        if ! docker info &> /dev/null; then
            echo -e "${RED}Error: Docker is not running${NC}"
            echo "Please start Docker and try again."
            exit 1
        fi

        # Check if k3d is installed
        if ! command_exists k3d; then
            echo -e "${YELLOW}k3d not found. Installing...${NC}"
            curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
        fi

        # Prompt for cluster name
        read -p "Enter cluster name [assocore-dev]: " CLUSTER_NAME
        CLUSTER_NAME=${CLUSTER_NAME:-assocore-dev}

        # Run k3d installation script
        echo ""
        if ! bash "$SCRIPT_DIR/install-k3d.sh" "$CLUSTER_NAME"; then
            echo -e "${RED}Error: k3d installation failed${NC}"
            echo "Please check the error messages above and try again."
            exit 1
        fi

    elif [ "$CLUSTER_TYPE" = "k3s" ]; then
        echo -e "${YELLOW}Installing k3s requires sudo access${NC}"

        if ! command_exists k3s; then
            echo -e "${BLUE}Installing k3s...${NC}"
            curl -sfL https://get.k3s.io | sh -

            # Configure kubectl for k3s
            mkdir -p ~/.kube
            sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
            sudo chown $USER:$USER ~/.kube/config
            chmod 600 ~/.kube/config
            export KUBECONFIG=~/.kube/config
        else
            echo -e "${GREEN}✓ k3s already installed${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}✓ Cluster ready${NC}"
fi

# Verify cluster access
echo ""
echo -e "${BLUE}Verifying cluster access...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to cluster${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if KUBECONFIG is set:"
    echo "     echo \$KUBECONFIG"
    echo "  2. Set it manually:"
    echo "     export KUBECONFIG=~/.kube/config"
    echo "  3. See docs/KUBECTL_CONNECTION_FIX.md for more help"
    exit 1
fi
echo -e "${GREEN}✓ Cluster accessible${NC}"
echo ""

# ==============================================================================
# STEP 2: Configuration
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 2: Configuration${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if .env already exists
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Found existing .env file${NC}"
    cat "$ENV_FILE"
    echo ""

    if prompt_yes_no "Use this existing configuration?" "y"; then
        echo -e "${GREEN}✓ Using existing .env${NC}"
        SKIP_CONFIG=true

        # Check if GHCR credentials are in the existing .env
        if grep -q "^GITHUB_USER=" "$ENV_FILE" && grep -q "^GITHUB_TOKEN=" "$ENV_FILE"; then
            SKIP_GHCR=false
        else
            SKIP_GHCR=true
        fi
    else
        echo -e "${YELLOW}Will create new configuration${NC}"
        SKIP_CONFIG=false
        SKIP_GHCR=false  # Will be set during configuration
        # Backup existing .env
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓ Backed up existing .env${NC}"
    fi
else
    SKIP_CONFIG=false
    SKIP_GHCR=false  # Will be set during configuration
fi

if [ "$SKIP_CONFIG" = false ]; then
    echo "Let's configure your deployment..."
    echo ""

    # Development vs Production
    echo -e "${YELLOW}Choose deployment mode:${NC}"
    echo -e "  ${GREEN}1)${NC} Development (HTTP, localhost/IP access)"
    echo -e "  ${GREEN}2)${NC} Production (HTTPS, with Let's Encrypt certificates)"
    echo ""

    while true; do
        read -p "Enter choice [1-2]: " mode_choice
        case $mode_choice in
            1)
                DEPLOYMENT_MODE="dev"
                break
                ;;
            2)
                DEPLOYMENT_MODE="prod"
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1 or 2.${NC}"
                ;;
        esac
    done

    echo ""

    # Domain configuration for production
    if [ "$DEPLOYMENT_MODE" = "prod" ]; then
        echo -e "${YELLOW}Domain Configuration${NC}"
        echo ""
        read -p "Enter your domain name (e.g., assocore.org): " DOMAIN_NAME
        read -p "Enter email for Let's Encrypt notifications: " LETSENCRYPT_EMAIL
        echo ""
    fi

    # GitHub Container Registry (REQUIRED for Backend/Frontend)
    echo -e "${YELLOW}GitHub Container Registry (GHCR)${NC}"
    echo "⚠️  REQUIRED for Backend and Frontend deployments"
    echo "GHCR is used to pull private Docker images from GitHub Container Registry"
    echo ""
    echo "To create a Personal Access Token (PAT):"
    echo "  1. Go to: https://github.com/settings/tokens/new"
    echo "  2. Select scope: read:packages"
    echo "  3. Generate and copy the token"
    echo ""

    SKIP_GHCR=false
    if prompt_yes_no "Configure GitHub Container Registry credentials?" "y"; then
        echo ""
        read -p "GitHub username: " GITHUB_USER
        read -p "GitHub Personal Access Token (PAT): " -s GITHUB_TOKEN
        echo ""
        echo ""
    else
        echo ""
        echo -e "${RED}⚠️  WARNING: Backend and Frontend deployments will FAIL without GHCR credentials!${NC}"
        echo ""
        echo "The following images require authentication:"
        echo "  - ghcr.io/assocore/assocore/backend:latest"
        echo "  - ghcr.io/assocore/assocore/frontend:latest"
        echo ""
        echo "You can add credentials later with:"
        echo "  ./k8s/01-secrets/create-ghcr-secret.sh <username> <token>"
        echo ""

        if prompt_yes_no "Are you sure you want to skip GHCR configuration?" "n"; then
            echo -e "${YELLOW}⊘ Skipping GHCR configuration${NC}"
            SKIP_GHCR=true
            GITHUB_USER=""
            GITHUB_TOKEN=""
        else
            echo -e "${YELLOW}Let's configure GHCR credentials...${NC}"
            echo ""
            read -p "GitHub username: " GITHUB_USER
            read -p "GitHub Personal Access Token (PAT): " -s GITHUB_TOKEN
            echo ""
            echo ""
            SKIP_GHCR=false
        fi
    fi

    # Database credentials
    echo -e "${YELLOW}Database Credentials${NC}"
    echo ""

    read -p "MariaDB database name [assocore]: " MARIADB_DATABASE
    MARIADB_DATABASE=${MARIADB_DATABASE:-assocore}

    read -p "MariaDB username [assocore]: " MARIADB_USER
    MARIADB_USER=${MARIADB_USER:-assocore}

    prompt_password "MARIADB_PASSWORD" "MariaDB password"
    echo ""

    prompt_password "MARIADB_ROOT_PASSWORD" "MariaDB root password"
    echo ""

    # Nextcloud credentials
    echo -e "${YELLOW}Nextcloud Admin Credentials${NC}"
    echo ""

    read -p "Nextcloud admin username [admin]: " NEXTCLOUD_ADMIN_USER
    NEXTCLOUD_ADMIN_USER=${NEXTCLOUD_ADMIN_USER:-admin}

    prompt_password "NEXTCLOUD_ADMIN_PASSWORD" "Nextcloud admin password"
    echo ""

    # Grafana credentials
    echo -e "${YELLOW}Grafana Admin Credentials${NC}"
    echo ""

    read -p "Grafana admin username [admin]: " GRAFANA_ADMIN_USER
    GRAFANA_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}

    prompt_password "GRAFANA_ADMIN_PASSWORD" "Grafana admin password"
    echo ""

    # Traefik dashboard credentials
    echo -e "${YELLOW}Traefik Dashboard Credentials${NC}"
    echo ""

    read -p "Traefik dashboard username [admin]: " TRAEFIK_DASHBOARD_USER
    TRAEFIK_DASHBOARD_USER=${TRAEFIK_DASHBOARD_USER:-admin}

    prompt_password "TRAEFIK_DASHBOARD_PASSWORD" "Traefik dashboard password"
    echo ""

    # Create .env file
    echo -e "${BLUE}Creating .env file...${NC}"

    cat > "$ENV_FILE" <<EOF
# AssoCORE Environment Configuration
# Generated on $(date)

# Deployment Mode: $DEPLOYMENT_MODE
DEPLOYMENT_MODE=$DEPLOYMENT_MODE

EOF

    # Add GitHub credentials only if configured
    if [ "$SKIP_GHCR" = false ]; then
        cat >> "$ENV_FILE" <<EOF
# GitHub Container Registry
GITHUB_USER=$GITHUB_USER
GITHUB_TOKEN=$GITHUB_TOKEN

EOF
    fi

    # MariaDB Database
    cat >> "$ENV_FILE" <<EOF
# MariaDB Database
MARIADB_ROOT_PASSWORD=$MARIADB_ROOT_PASSWORD
MARIADB_DATABASE=$MARIADB_DATABASE
MARIADB_USER=$MARIADB_USER
MARIADB_PASSWORD=$MARIADB_PASSWORD

# Nextcloud
NEXTCLOUD_ADMIN_USER=$NEXTCLOUD_ADMIN_USER
NEXTCLOUD_ADMIN_PASSWORD=$NEXTCLOUD_ADMIN_PASSWORD

# Grafana
GRAFANA_ADMIN_USER=$GRAFANA_ADMIN_USER
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Traefik Dashboard
TRAEFIK_DASHBOARD_USER=$TRAEFIK_DASHBOARD_USER
TRAEFIK_DASHBOARD_PASSWORD=$TRAEFIK_DASHBOARD_PASSWORD
EOF

    if [ "$DEPLOYMENT_MODE" = "prod" ]; then
        cat >> "$ENV_FILE" <<EOF

# Production Domain Configuration
DOMAIN_NAME=$DOMAIN_NAME
LETSENCRYPT_EMAIL=$LETSENCRYPT_EMAIL
EOF
    fi

    echo -e "${GREEN}✓ Configuration saved to $ENV_FILE${NC}"
    echo ""

    # Show warning about secrets
    echo -e "${YELLOW}⚠️  IMPORTANT: Keep your .env file secure!${NC}"
    echo "   - It contains sensitive credentials"
    echo "   - Do NOT commit it to Git (it's in .gitignore)"
    echo "   - Back it up securely"
    echo ""

    read -p "Press Enter to continue..."
    echo ""
fi

# ==============================================================================
# STEP 3: Namespace Creation
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 3: Creating Namespace${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Namespace '$NAMESPACE' already exists${NC}"
else
    echo -e "${BLUE}Creating namespace '$NAMESPACE'...${NC}"
    kubectl apply -f "$SCRIPT_DIR/00-namespace/"
    echo -e "${GREEN}✓ Namespace created${NC}"
fi
echo ""

# ==============================================================================
# STEP 4: Secrets Creation
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 4: Creating Kubernetes Secrets${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}Creating secrets from .env file...${NC}"
bash "$SCRIPT_DIR/01-secrets/create-app-secrets.sh"
echo -e "${GREEN}✓ All secrets created${NC}"
echo ""

# ==============================================================================
# STEP 5: Core Services Deployment
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 5: Deploying Core Services${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Core services include:"
echo "  - Traefik (Ingress Controller)"
echo "  - Prometheus (Metrics)"
echo "  - Grafana (Monitoring Dashboard)"
echo "  - Watchtower (Image Updater - disabled by default)"
echo ""

if prompt_yes_no "Deploy core services now?" "y"; then
    echo ""
    if ! bash "$SCRIPT_DIR/deploy-core-services.sh"; then
        echo -e "${RED}Error: Core services deployment failed${NC}"
        echo "Please check the error messages above."
        echo "You can retry with: ./k8s/deploy-core-services.sh"
        exit 1
    fi
    echo -e "${GREEN}✓ Core services deployed${NC}"
else
    echo -e "${YELLOW}⊘ Skipping core services${NC}"
    echo "You can deploy them later with: ./k8s/deploy-core-services.sh"
fi
echo ""

# ==============================================================================
# STEP 6: Application Deployment
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 6: Deploying Applications${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Applications include:"
echo "  - MariaDB (Database)"
echo "  - Redis (Cache)"
echo "  - Backend API (FastAPI)"
echo "  - Frontend (Next.js)"
echo "  - Nextcloud (File Storage)"
echo ""

if prompt_yes_no "Deploy applications now?" "y"; then
    # The deploy-apps.sh script handles secrets internally but we've already created them
    # Just run the deployment parts

    echo -e "${YELLOW}Deploying MariaDB...${NC}"
    kubectl apply -f "$SCRIPT_DIR/07-database/mariadb-config.yaml"
    kubectl apply -f "$SCRIPT_DIR/07-database/mariadb-statefulset.yaml"
    echo "Waiting for MariaDB to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mariadb -n $NAMESPACE --timeout=300s
    echo -e "${GREEN}✓ MariaDB ready${NC}"
    echo ""

    echo -e "${YELLOW}Deploying Redis...${NC}"
    kubectl apply -f "$SCRIPT_DIR/08-redis/"
    echo "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n $NAMESPACE --timeout=120s
    echo -e "${GREEN}✓ Redis ready${NC}"
    echo ""

    # Check for GHCR secret before deploying Backend/Frontend
    DEPLOY_BACKEND_FRONTEND=true
    if ! kubectl get secret ghcr-secret -n $NAMESPACE &>/dev/null; then
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}⚠️  CRITICAL: GHCR Secret Not Found${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Backend and Frontend require 'ghcr-secret' to pull private images."
        echo ""
        echo "Options:"
        echo "  1) Create the secret now (recommended)"
        echo "  2) Skip Backend/Frontend deployment"
        echo ""

        if prompt_yes_no "Create GHCR secret now?" "y"; then
            echo ""
            read -p "GitHub username: " GITHUB_USER_NOW
            read -p "GitHub Personal Access Token (PAT): " -s GITHUB_TOKEN_NOW
            echo ""
            echo ""

            if [ -n "$GITHUB_USER_NOW" ] && [ -n "$GITHUB_TOKEN_NOW" ]; then
                bash "$SCRIPT_DIR/01-secrets/create-ghcr-secret.sh" "$GITHUB_USER_NOW" "$GITHUB_TOKEN_NOW" "$NAMESPACE"
                DEPLOY_BACKEND_FRONTEND=true
                echo ""
            else
                echo -e "${RED}Error: GitHub credentials cannot be empty${NC}"
                echo -e "${YELLOW}⊘ Skipping Backend and Frontend deployment${NC}"
                DEPLOY_BACKEND_FRONTEND=false
                echo ""
            fi
        else
            echo -e "${YELLOW}⊘ Skipping Backend and Frontend deployment${NC}"
            DEPLOY_BACKEND_FRONTEND=false
            echo ""
            echo "To deploy later:"
            echo "  1. Create secret: ./k8s/01-secrets/create-ghcr-secret.sh <user> <token>"
            echo "  2. Deploy Backend: kubectl apply -f k8s/09-backend/"
            echo "  3. Deploy Frontend: kubectl apply -f k8s/10-frontend/"
            echo ""
        fi
    fi

    # Deploy Backend if secret exists
    if [ "$DEPLOY_BACKEND_FRONTEND" = true ]; then
        echo -e "${YELLOW}Deploying Backend API...${NC}"
        kubectl apply -f "$SCRIPT_DIR/09-backend/backend-config.yaml"
        kubectl apply -f "$SCRIPT_DIR/09-backend/backend-deployment.yaml"
        echo "Waiting for Backend to be ready..."
        kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s
        echo -e "${GREEN}✓ Backend ready${NC}"
        echo ""

        echo -e "${YELLOW}Deploying Frontend...${NC}"
        kubectl apply -f "$SCRIPT_DIR/10-frontend/"
        echo "Waiting for Frontend to be ready..."
        kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s
        echo -e "${GREEN}✓ Frontend ready${NC}"
        echo ""
    fi

    echo -e "${YELLOW}Deploying Nextcloud...${NC}"
    kubectl apply -f "$SCRIPT_DIR/11-nextcloud/nextcloud-config.yaml"
    kubectl apply -f "$SCRIPT_DIR/11-nextcloud/nextcloud-statefulset.yaml"
    echo "Waiting for Nextcloud to be ready (this may take a few minutes)..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=nextcloud -n $NAMESPACE --timeout=600s
    echo -e "${GREEN}✓ Nextcloud ready${NC}"
    echo ""

    echo -e "${YELLOW}Deploying Ingress Routes...${NC}"
    kubectl apply -f "$SCRIPT_DIR/12-ingress-apps/"
    echo -e "${GREEN}✓ Ingress routes applied${NC}"
    echo ""
else
    echo -e "${YELLOW}⊘ Skipping application deployment${NC}"
    echo "You can deploy them later with: ./k8s/deploy-apps.sh"
fi
echo ""

# ==============================================================================
# STEP 7: Summary and Access Information
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}DEPLOYMENT COMPLETE! 🎉${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get cluster info
if [ "$CLUSTER_TYPE" = "k3d" ]; then
    # For k3d, we need to get the mapped port
    TRAEFIK_PORT=$(kubectl get svc -n kube-system traefik -o jsonpath='{.spec.ports[?(@.name=="web")].nodePort}' 2>/dev/null || echo "80")
    TRAEFIK_HTTPS_PORT=$(kubectl get svc -n kube-system traefik -o jsonpath='{.spec.ports[?(@.name=="websecure")].nodePort}' 2>/dev/null || echo "443")
    ACCESS_HOST="localhost"
elif [ "$CLUSTER_TYPE" = "k3s" ]; then
    ACCESS_HOST=$(hostname -I | awk '{print $1}')
    TRAEFIK_PORT="80"
    TRAEFIK_HTTPS_PORT="443"
else
    ACCESS_HOST="localhost"
    TRAEFIK_PORT="80"
    TRAEFIK_HTTPS_PORT="443"
fi

# Determine protocol
if [ "$DEPLOYMENT_MODE" = "prod" ]; then
    PROTOCOL="https"
    PORT_SUFFIX=""
    BASE_URL="https://$DOMAIN_NAME"
else
    PROTOCOL="http"
    if [ "$TRAEFIK_PORT" != "80" ]; then
        PORT_SUFFIX=":$TRAEFIK_PORT"
    else
        PORT_SUFFIX=""
    fi
    BASE_URL="http://$ACCESS_HOST$PORT_SUFFIX"
fi

echo -e "${GREEN}✓ AssoCORE is now running!${NC}"
echo ""
echo -e "${YELLOW}Access Information:${NC}"
echo ""

# Source .env to get credentials for display
source "$ENV_FILE"

echo -e "${CYAN}📊 Grafana Monitoring Dashboard${NC}"
echo "   URL: ${BASE_URL}/grafana/"
echo "   Username: ${GRAFANA_ADMIN_USER}"
echo "   Password: ${GRAFANA_ADMIN_PASSWORD}"
echo ""

echo -e "${CYAN}🔀 Traefik Dashboard${NC}"
echo "   URL: ${BASE_URL}/dashboard/"
echo "   Username: ${TRAEFIK_DASHBOARD_USER}"
echo "   Password: ${TRAEFIK_DASHBOARD_PASSWORD}"
echo ""

echo -e "${CYAN}🌐 Frontend Application${NC}"
echo "   URL: ${BASE_URL}/"
echo ""

echo -e "${CYAN}🔧 Backend API${NC}"
echo "   URL: ${BASE_URL}/api/"
echo "   Docs: ${BASE_URL}/api/docs"
echo ""

echo -e "${CYAN}☁️  Nextcloud${NC}"
echo "   URL: ${BASE_URL}/nextcloud/"
echo "   Username: ${NEXTCLOUD_ADMIN_USER}"
echo "   Password: ${NEXTCLOUD_ADMIN_PASSWORD}"
echo ""

# Note if GHCR was skipped
if [ "$SKIP_GHCR" = true ]; then
    echo -e "${YELLOW}⚠️  Note: GitHub Container Registry (GHCR) was not configured${NC}"
    echo "   If you need to pull private images from GHCR, run:"
    echo "   ./k8s/01-secrets/create-ghcr-secret.sh <username> <token>"
    echo ""
fi

echo -e "${YELLOW}Kubernetes Management:${NC}"
echo ""
echo "  Check pod status:"
echo "    kubectl get pods -n $NAMESPACE"
echo ""
echo "  View logs:"
echo "    kubectl logs -n $NAMESPACE <pod-name>"
echo ""
echo "  Restart a deployment:"
echo "    kubectl rollout restart deployment/<name> -n $NAMESPACE"
echo ""

if [ "$DEPLOYMENT_MODE" = "prod" ]; then
    echo -e "${YELLOW}⚠️  Production Checklist:${NC}"
    echo "  - Ensure DNS records point to this server"
    echo "  - Wait for Let's Encrypt certificates (may take a few minutes)"
    echo "  - Check certificate status:"
    echo "    kubectl get certificate -n $NAMESPACE"
    echo ""
fi

echo -e "${YELLOW}📚 Documentation:${NC}"
echo "  - Complete testing guide: docs/src/content/docs/guides/how-to/testing-deployment.mdx"
echo "  - Troubleshooting: docs/COMMON_ISSUES.md"
echo "  - kubectl connection issues: docs/KUBECTL_CONNECTION_FIX.md"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Save deployment info
DEPLOY_INFO_FILE="$SCRIPT_DIR/.deployment-info"
cat > "$DEPLOY_INFO_FILE" <<EOF
# AssoCORE Deployment Information
# Generated on $(date)

CLUSTER_TYPE=$CLUSTER_TYPE
DEPLOYMENT_MODE=$DEPLOYMENT_MODE
ACCESS_HOST=$ACCESS_HOST
TRAEFIK_PORT=$TRAEFIK_PORT
BASE_URL=$BASE_URL
NAMESPACE=$NAMESPACE

# Access URLs
GRAFANA_URL=${BASE_URL}/grafana/
TRAEFIK_URL=${BASE_URL}/dashboard/
FRONTEND_URL=${BASE_URL}/
BACKEND_URL=${BASE_URL}/api/
NEXTCLOUD_URL=${BASE_URL}/nextcloud/
EOF

echo -e "${BLUE}ℹ️  Deployment info saved to: $DEPLOY_INFO_FILE${NC}"
echo ""
