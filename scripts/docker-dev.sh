#!/bin/bash
# AssoCORE Docker Development Environment Setup
# Quick start script for local development with hot-reload
#
# Usage: ./scripts/docker-dev.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${GREEN}AssoCORE Development Environment${CYAN}                  ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Quick start for local development with hot-reload        ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

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

echo ""

# ==============================================================================
# STEP 2: Environment Configuration
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 2: Environment Configuration${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

ENV_FILE="$SCRIPT_DIR/back/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo ""
    echo "Creating basic development .env file..."
    
    # Generate secure random passwords
    MARIA_ROOT_PASS=$(openssl rand -base64 32)
    MARIA_USER_PASS=$(openssl rand -base64 32)
    
    cat > "$ENV_FILE" <<EOF
# AssoCORE Development Environment Configuration
# Generated on $(date)

# Database Configuration
MARIADB_ROOT_PASSWORD=$MARIA_ROOT_PASS
NEXTCLOUD_DB_NAME=nextcloud_dev
NEXTCLOUD_DB_USER=nextcloud_dev
NEXTCLOUD_DB_PASSWORD=$MARIA_USER_PASS

# Backend Configuration
DATABASE_URL=mysql+aiomysql://nextcloud_dev:$MARIA_USER_PASS@db:3306/nextcloud_dev
ENVIRONMENT=development

# Nextcloud Configuration
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=admin123

# Optional: JWT Secret
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
    
    echo -e "${GREEN}✓ Created .env file with secure passwords${NC}"
    echo ""
    echo -e "${YELLOW}Note: Default Nextcloud credentials created:${NC}"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
else
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo ""
fi

# ==============================================================================
# STEP 3: Create Directories
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 3: Creating Data Directories${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

mkdir -p "$SCRIPT_DIR/data/db"
mkdir -p "$SCRIPT_DIR/data/nextcloud"
mkdir -p "$SCRIPT_DIR/build/mobile"

echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# ==============================================================================
# STEP 4: Start Development Services
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 4: Starting Development Services${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$SCRIPT_DIR"

echo "Which services would you like to start?"
echo ""
echo "  1) Full stack (all services)"
echo "  2) Backend only (API + Database + Redis)"
echo "  3) Frontend only (Next.js + Backend)"
echo "  4) Infrastructure only (Database + Redis + Nextcloud)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        SERVICES=""
        SERVICE_DESC="full stack"
        ;;
    2)
        SERVICES="db redis backend"
        SERVICE_DESC="backend services"
        ;;
    3)
        SERVICES="db redis backend frontend"
        SERVICE_DESC="frontend + backend"
        ;;
    4)
        SERVICES="db redis nextcloud"
        SERVICE_DESC="infrastructure only"
        ;;
    *)
        echo -e "${RED}Invalid choice. Starting full stack.${NC}"
        SERVICES=""
        SERVICE_DESC="full stack"
        ;;
esac

echo ""
echo -e "${BLUE}Starting $SERVICE_DESC...${NC}"
echo ""

# Start services
if [ -z "$SERVICES" ]; then
    docker compose up --build $SERVICES
else
    docker compose up --build $SERVICES
fi

# Note: Script ends here when docker compose exits
# The following code runs only if user stops the services

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Services Stopped${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

read -p "Remove containers? [y/N]: " remove
if [[ $remove =~ ^[Yy]$ ]]; then
    docker compose down
    echo -e "${GREEN}✓ Containers removed${NC}"
else
    echo -e "${YELLOW}Containers preserved (use 'docker compose down' to remove)${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Development session ended${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
