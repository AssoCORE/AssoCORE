#!/bin/bash
# AssoCORE Complete Docker Deployment Script
# Interactive guided setup for development or production deployment
#
# Usage: ./scripts/docker-deploy.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

# ==============================================================================
# Helper Functions
# ==============================================================================

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

prompt_password() {
    local var_name="$1"
    local prompt_text="$2"
    local password
    local password_confirm

    while true; do
        read -sp "$prompt_text: " password
        echo ""
        read -sp "Confirm password: " password_confirm
        echo ""

        if [ "$password" = "$password_confirm" ]; then
            if [ ${#password} -lt 8 ]; then
                echo -e "${RED}Password must be at least 8 characters${NC}"
                continue
            fi
            eval "$var_name='$password'"
            break
        else
            echo -e "${RED}Passwords do not match. Try again.${NC}"
        fi
    done
}

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${GREEN}AssoCORE Complete Docker Deployment${CYAN}              ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Interactive guided setup for development or production    ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "This script will guide you through deploying AssoCORE with Docker."
echo ""

# ==============================================================================
# STEP 0: Clean Start Option
# ==============================================================================

echo -e "${YELLOW}⚠️  Clean Start Option${NC}"
echo ""
echo "Do you want to perform a clean start?"
echo "This will:"
echo "  - Stop and remove all running containers"
echo "  - Remove Docker volumes (⚠️ DATA LOSS)"
echo "  - Delete existing .env configuration"
echo ""
echo -e "${RED}WARNING: This will delete all existing data!${NC}"
echo ""

if prompt_yes_no "Perform clean start?" "n"; then
    echo ""
    echo -e "${BLUE}Performing clean start...${NC}"
    echo ""
    
    # Stop and remove containers
    if docker compose ps -q &> /dev/null; then
        echo -e "${YELLOW}Stopping Docker services...${NC}"
        docker compose down -v || true
        docker compose --profile prod down -v || true
        echo -e "${GREEN}✓ Containers stopped and removed${NC}"
    fi
    
    # Remove .env
    if [ -f "$SCRIPT_DIR/back/.env" ]; then
        BACKUP_NAME="$SCRIPT_DIR/back/.env.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$SCRIPT_DIR/back/.env" "$BACKUP_NAME"
        rm "$SCRIPT_DIR/back/.env"
        echo -e "${GREEN}✓ .env backed up to ${BACKUP_NAME}${NC}"
    fi
    
    # Clean data directories (ask for confirmation)
    if prompt_yes_no "Delete data directories (database, nextcloud)?" "n"; then
        rm -rf "$SCRIPT_DIR/data/"
        echo -e "${GREEN}✓ Data directories cleaned${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Clean start complete${NC}"
    echo ""
fi

# ==============================================================================
# STEP 1: Prerequisites Check
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 1: Checking Prerequisites${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Error: Docker Compose is not available${NC}"
    echo "Please install Docker Compose V2"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Error: Docker daemon is not running${NC}"
    echo "Please start Docker service"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Check disk space
AVAILABLE_SPACE=$(df -h "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
echo -e "${GREEN}✓ Available disk space: $AVAILABLE_SPACE${NC}"

echo ""

# ==============================================================================
# STEP 2: Configuration
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 2: Configuration${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

ENV_FILE="$SCRIPT_DIR/back/.env"
SKIP_CONFIG=false

# Check if .env exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Found existing .env file${NC}"
    echo ""
    
    if prompt_yes_no "Use existing configuration?" "y"; then
        echo -e "${GREEN}✓ Using existing .env${NC}"
        SKIP_CONFIG=true
    else
        echo -e "${YELLOW}Will create new configuration${NC}"
        BACKUP_NAME="$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$ENV_FILE" "$BACKUP_NAME"
        echo -e "${GREEN}✓ Backed up existing .env to ${BACKUP_NAME}${NC}"
        SKIP_CONFIG=false
    fi
else
    SKIP_CONFIG=false
fi

echo ""

if [ "$SKIP_CONFIG" = false ]; then
    echo "Let's configure your deployment..."
    echo ""
    
    # Deployment mode
    echo -e "${YELLOW}Choose deployment mode:${NC}"
    echo -e "  ${GREEN}1)${NC} Development (hot-reload, debug builds)"
    echo -e "  ${GREEN}2)${NC} Production (optimized, release builds)"
    echo ""
    
    while true; do
        read -p "Enter choice [1-2]: " mode_choice
        case $mode_choice in
            1)
                DEPLOYMENT_MODE="development"
                DEPLOYMENT_PROFILE=""
                break
                ;;
            2)
                DEPLOYMENT_MODE="production"
                DEPLOYMENT_PROFILE="--profile prod"
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1 or 2.${NC}"
                ;;
        esac
    done
    
    echo ""
    
    # Database credentials
    echo -e "${YELLOW}Database Configuration${NC}"
    echo ""
    
    read -p "MariaDB database name [nextcloud_${DEPLOYMENT_MODE}]: " MARIADB_DATABASE
    MARIADB_DATABASE=${MARIADB_DATABASE:-nextcloud_${DEPLOYMENT_MODE}}
    
    read -p "MariaDB username [nextcloud_user]: " MARIADB_USER
    MARIADB_USER=${MARIADB_USER:-nextcloud_user}
    
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        echo ""
        echo "For production, using auto-generated secure passwords"
        MARIADB_ROOT_PASSWORD=$(openssl rand -base64 32)
        MARIADB_PASSWORD=$(openssl rand -base64 32)
        echo -e "${GREEN}✓ Generated secure passwords${NC}"
    else
        echo ""
        prompt_password "MARIADB_ROOT_PASSWORD" "MariaDB root password"
        echo ""
        prompt_password "MARIADB_PASSWORD" "MariaDB user password"
    fi
    echo ""
    
    # Nextcloud credentials
    echo -e "${YELLOW}Nextcloud Admin Credentials${NC}"
    echo ""
    
    read -p "Nextcloud admin username [admin]: " NEXTCLOUD_ADMIN_USER
    NEXTCLOUD_ADMIN_USER=${NEXTCLOUD_ADMIN_USER:-admin}
    
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        NEXTCLOUD_ADMIN_PASSWORD=$(openssl rand -base64 16)
        echo -e "${GREEN}✓ Generated secure admin password${NC}"
    else
        echo ""
        prompt_password "NEXTCLOUD_ADMIN_PASSWORD" "Nextcloud admin password"
    fi
    echo ""
    
    # Create .env file
    echo -e "${BLUE}Creating .env file...${NC}"
    
    cat > "$ENV_FILE" <<EOF
# AssoCORE Environment Configuration
# Generated on $(date)

# Deployment Mode: $DEPLOYMENT_MODE
ENVIRONMENT=$DEPLOYMENT_MODE

# Database Configuration
MARIADB_ROOT_PASSWORD=$MARIADB_ROOT_PASSWORD
NEXTCLOUD_DB_NAME=$MARIADB_DATABASE
NEXTCLOUD_DB_USER=$MARIADB_USER
NEXTCLOUD_DB_PASSWORD=$MARIADB_PASSWORD

# Backend Configuration
DATABASE_URL=mysql+aiomysql://${MARIADB_USER}:${MARIADB_PASSWORD}@db:3306/${MARIADB_DATABASE}

# Nextcloud Configuration
NEXTCLOUD_ADMIN_USER=$NEXTCLOUD_ADMIN_USER
NEXTCLOUD_ADMIN_PASSWORD=$NEXTCLOUD_ADMIN_PASSWORD

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
    
    echo -e "${GREEN}✓ Configuration saved to $ENV_FILE${NC}"
    echo ""
    
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        echo -e "${YELLOW}⚠️  IMPORTANT: Production credentials generated${NC}"
        echo ""
        echo "MariaDB Root Password: $MARIADB_ROOT_PASSWORD"
        echo "MariaDB User Password: $MARIADB_PASSWORD"
        echo "Nextcloud Admin Username: $NEXTCLOUD_ADMIN_USER"
        echo "Nextcloud Admin Password: $NEXTCLOUD_ADMIN_PASSWORD"
        echo ""
        echo -e "${RED}SAVE THESE CREDENTIALS SECURELY!${NC}"
        echo ""
        read -p "Press Enter when you have saved the credentials..."
        echo ""
    fi
else
    # Load existing config to determine mode
    source "$ENV_FILE"
    if [ "$ENVIRONMENT" = "production" ]; then
        DEPLOYMENT_MODE="production"
        DEPLOYMENT_PROFILE="--profile prod"
    else
        DEPLOYMENT_MODE="development"
        DEPLOYMENT_PROFILE=""
    fi
fi

# ==============================================================================
# STEP 3: Prepare Directories
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 3: Preparing Directories${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

mkdir -p "$SCRIPT_DIR/data/db"
mkdir -p "$SCRIPT_DIR/data/nextcloud"
mkdir -p "$SCRIPT_DIR/build/mobile"

echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# ==============================================================================
# STEP 4: Build Images
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 4: Building Docker Images${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$SCRIPT_DIR"

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo -e "${BLUE}Building images for ${DEPLOYMENT_MODE} mode...${NC}"
echo ""

if [ "$DEPLOYMENT_MODE" = "production" ]; then
    docker compose --profile prod build
else
    docker compose build
fi

echo ""
echo -e "${GREEN}✓ Images built successfully${NC}"
echo ""

# ==============================================================================
# STEP 5: Deploy Services
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 5: Deploying Services${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

if prompt_yes_no "Start services now?" "y"; then
    echo ""
    echo -e "${BLUE}Starting services in ${DEPLOYMENT_MODE} mode...${NC}"
    echo ""
    
    # Start in detached mode
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        docker compose --profile prod up -d
    else
        docker compose up -d
    fi
    
    echo ""
    echo -e "${YELLOW}Waiting for services to initialize...${NC}"
    sleep 10
    
    # Wait for database
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    until docker compose exec db mariadb-admin ping -h"localhost" --silent 2>/dev/null; do
        sleep 2
        echo -n "."
    done
    echo ""
    echo -e "${GREEN}✓ Database is ready${NC}"
    
    # Wait for backend health
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        SERVICE_NAME="backend_prod"
    else
        SERVICE_NAME="backend"
    fi
    
    echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
    for i in {1..30}; do
        if curl-s http://localhost:8000/health &> /dev/null; then
            echo -e "${GREEN}✓ Backend is ready${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    
    echo -e "${GREEN}✓ All services deployed${NC}"
else
    echo -e "${YELLOW}⊘ Skipping service startup${NC}"
    echo "You can start services later with:"
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        echo "  docker compose --profile prod up -d"
    else
        echo "  docker compose up -d"
    fi
fi

echo ""

# ==============================================================================
# STEP 6: Summary
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}DEPLOYMENT COMPLETE! 🎉${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}✓ AssoCORE is now running in ${DEPLOYMENT_MODE} mode!${NC}"
echo ""

# Load credentials
source "$ENV_FILE"

echo -e "${YELLOW}Access Information:${NC}"
echo ""

if docker compose ps | grep -q "frontend"; then
    echo -e "${CYAN}🌐 Frontend Application${NC}"
    echo "   URL: http://localhost:3000"
    echo ""
fi

if docker compose ps | grep -q "backend"; then
    echo -e "${CYAN}🔧 Backend API${NC}"
    echo "   URL: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
    echo "   ReDoc: http://localhost:8000/redoc"
    echo ""
fi

echo -e "${CYAN}☁️  Nextcloud${NC}"
echo "   URL: http://localhost:8081"
echo "   Username: ${NEXTCLOUD_ADMIN_USER}"
if [ "$DEPLOYMENT_MODE" = "development" ]; then
    echo "   Password: ${NEXTCLOUD_ADMIN_PASSWORD}"
else
    echo "   Password: (see credentials above)"
fi
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo "  View logs (all):      docker compose logs -f"
echo "  View logs (backend):  docker compose logs -f ${SERVICE_NAME}"
echo "  Check status:         docker compose ps"
echo "  Stop services:        docker compose down"
if [ "$DEPLOYMENT_MODE" = "production" ]; then
    echo "  Restart service:      docker compose --profile prod restart backend_prod"
else
    echo "  Restart service:      docker compose restart backend"
fi
echo "  Shell into backend:   docker compose exec ${SERVICE_NAME} sh"
echo "  Database shell:       docker compose exec db mysql -u root -p"
echo ""

echo -e "${YELLOW}📚 Documentation:${NC}"
echo "  - Docker Guide: docs/src/content/docs/guides/how-to/docker-dev-prod.mdx"
echo "  - Quick Scripts: ./scripts/docker-dev.sh or ./scripts/docker-prod.sh"
echo "  - Docker README: docker/README.md"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
