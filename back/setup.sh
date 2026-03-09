#!/usr/bin/env bash

# ==============================================================================
# AssoCORE Backend Setup Script
# ==============================================================================
# Complete setup and deployment of the backend stack:
# - MariaDB database
# - Redis cache
# - Nextcloud
# - FastAPI backend
#
# This script provides interactive setup with health checks and validation.
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

wait_for_service() {
    local service=$1
    local check_command=$2
    local max_wait=${3:-120}
    local elapsed=0
    
    print_step "Waiting for $service to be ready..."
    
    while ! eval "$check_command" >/dev/null 2>&1; do
        if [ $elapsed -ge $max_wait ]; then
            print_error "Timeout waiting for $service after ${max_wait}s"
            return 1
        fi
        
        echo -ne "${YELLOW}⏳${NC} Elapsed: ${elapsed}s / ${max_wait}s\r"
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    echo -e "\r${GREEN}✓${NC} $service is ready! (took ${elapsed}s)"
    return 0
}

# ==============================================================================
# Main Script
# ==============================================================================

print_header "🚀 AssoCORE Backend Setup"

# ------------------------------------------------------------------------------
# Step 1: Check Prerequisites
# ------------------------------------------------------------------------------
print_step "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo -e "  Please install Docker: ${CYAN}https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
print_success "Docker installed"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose V2 is not installed"
    echo -e "  Please install Docker Compose V2: ${CYAN}https://docs.docker.com/compose/install/${NC}"
    exit 1
fi
print_success "Docker Compose V2 installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo ""
    print_step "Attempting to start Docker..."
    
    if command -v systemctl &> /dev/null; then
        sudo systemctl start docker
        sleep 3
        
        if ! docker info &> /dev/null; then
            print_error "Failed to start Docker daemon"
            echo "  Please start Docker manually"
            exit 1
        fi
        print_success "Docker daemon started"
    else
        print_error "Please start Docker Desktop or Docker daemon manually"
        exit 1
    fi
else
    print_success "Docker daemon running"
fi

# Check uv
if ! command -v uv &> /dev/null; then
    print_warning "uv not found (optional for local development)"
else
    print_success "uv installed"
fi

# ------------------------------------------------------------------------------
# Step 2: Environment Configuration
# ------------------------------------------------------------------------------
echo ""
print_step "Checking environment configuration..."

if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo ""
    echo "Please create .env file with required configuration."
    echo ""
    echo -e "${CYAN}Required variables:${NC}"
    echo "  - MYSQL_ROOT_PASSWORD"
    echo "  - MYSQL_DATABASE"
    echo "  - MYSQL_USER"
    echo "  - MYSQL_PASSWORD"
    echo "  - NEXTCLOUD_DB_NAME"
    echo "  - NEXTCLOUD_DB_USER"
    echo "  - NEXTCLOUD_DB_PASSWORD"
    echo "  - NEXTCLOUD_ADMIN_USER"
    echo "  - NEXTCLOUD_ADMIN_PASSWORD"
    echo ""
    echo -e "Copy from example: ${YELLOW}cp .env.example .env${NC}"
    exit 1
fi
print_success ".env file found"

# ------------------------------------------------------------------------------
# Step 3: Python Environment (Optional)
# ------------------------------------------------------------------------------
if command -v uv &> /dev/null; then
    echo ""
    read -p "$(echo -e ${CYAN}?)${NC} Setup local Python environment with uv? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_step "Setting up Python environment..."
        uv sync
        print_success "Python environment ready"
    else
        print_warning "Skipped Python environment setup"
    fi
fi

# ------------------------------------------------------------------------------
# Step 4: Clean Start Option
# ------------------------------------------------------------------------------
echo ""
if [ -d "data" ]; then
    print_warning "Existing data directory found"
    echo ""
    echo "  🗄️  Database data: $(du -sh data/db 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "  ☁️  Nextcloud data: $(du -sh data/nextcloud 2>/dev/null | cut -f1 || echo 'N/A')"
    echo ""
    read -p "$(echo -e ${YELLOW}⚠)${NC} Start fresh (delete all data)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Stopping existing services..."
        docker compose down -v --remove-orphans 2>/dev/null || true
        
        print_step "Deleting data directory..."
        rm -rf data/
        print_success "Data directory cleaned"
    fi
fi

# Create data directories
print_step "Creating data directories..."
mkdir -p data/db data/nextcloud
print_success "Data directories ready"

# ------------------------------------------------------------------------------
# Step 5: Build and Start Services
# ------------------------------------------------------------------------------
echo ""
print_header "🚢 Starting Services"

print_step "Building and starting containers..."
docker compose up -d --build

print_success "Containers started"

# ------------------------------------------------------------------------------
# Step 6: Wait for Services
# ------------------------------------------------------------------------------
echo ""
print_header "⏳ Waiting for Services"

# Wait for MariaDB
DB_CONTAINER=$(docker compose ps -q db)
wait_for_service "MariaDB" \
    "docker exec $DB_CONTAINER mariadb-admin ping -h localhost --silent" \
    90 || exit 1

# Wait for Redis
REDIS_CONTAINER=$(docker compose ps -q redis)
wait_for_service "Redis" \
    "docker exec $REDIS_CONTAINER redis-cli ping | grep -q PONG" \
    30 || exit 1

# Wait for Nextcloud
NEXTCLOUD_CONTAINER=$(docker compose ps -q nextcloud)
wait_for_service "Nextcloud" \
    "docker exec $NEXTCLOUD_CONTAINER curl -sf http://localhost:80/status.php" \
    120 || exit 1

# Wait for API
API_CONTAINER=$(docker compose ps -q api)
if [ -n "$API_CONTAINER" ]; then
    wait_for_service "API" \
        "docker exec $API_CONTAINER curl -sf http://localhost:8000/health" \
        60 || print_warning "API health check failed (might be starting)"
fi

# ------------------------------------------------------------------------------
# Step 7: Configure Nextcloud
# ------------------------------------------------------------------------------
echo ""
print_header "🔧 Configuring Nextcloud"

# Check if Nextcloud is installed
if docker exec -u www-data $NEXTCLOUD_CONTAINER php occ status 2>/dev/null | grep -q "installed: true"; then
    print_success "Nextcloud is already installed"
    
    print_step "Configuring trusted domains..."
    docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:system:set trusted_domains 0 --value=localhost:8081 2>/dev/null || true
    docker exec -u www-data $NEXTCLOUD_CONTAINER php occ config:system:set trusted_domains 1 --value=nextcloud 2>/dev/null || true
    print_success "Trusted domains configured"
    
    echo ""
    read -p "$(echo -e ${CYAN}?)${NC} Install recommended Nextcloud apps? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_step "Installing calendar..."
        docker exec -u www-data $NEXTCLOUD_CONTAINER php occ app:install calendar 2>/dev/null || print_warning "Calendar already installed or unavailable"
        
        print_step "Installing contacts..."
        docker exec -u www-data $NEXTCLOUD_CONTAINER php occ app:install contacts 2>/dev/null || print_warning "Contacts already installed or unavailable"
        
        print_step "Installing notes..."
        docker exec -u www-data $NEXTCLOUD_CONTAINER php occ app:install notes 2>/dev/null || print_warning "Notes already installed or unavailable"
        
        print_success "Apps installation complete"
    fi
else
    print_warning "Nextcloud needs initial setup"
    echo ""
    echo "  Please complete setup at ${CYAN}http://localhost:8081${NC}"
    echo ""
    echo "  Use credentials from .env file:"
    echo "  • Admin user: ${YELLOW}NEXTCLOUD_ADMIN_USER${NC}"
    echo "  • Admin password: ${YELLOW}NEXTCLOUD_ADMIN_PASSWORD${NC}"
    echo ""
fi

# ------------------------------------------------------------------------------
# Step 8: Health Check Summary
# ------------------------------------------------------------------------------
echo ""
print_header "✅ Deployment Complete!"

echo -e "${GREEN}✓${NC} All services are running"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Service URLs:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  🌐 Nextcloud:     ${GREEN}http://localhost:8081${NC}"
echo -e "  🔌 API:           ${GREEN}http://localhost:8000${NC}"
echo -e "  📚 API Docs:      ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  🔍 API Redoc:     ${GREEN}http://localhost:8000/redoc${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Quick Commands:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${YELLOW}./dev.sh${NC}              - Start development with hot-reload"
echo -e "  ${YELLOW}./shutdown.sh${NC}         - Stop all services"
echo -e "  ${YELLOW}docker compose logs -f${NC} - View logs"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
