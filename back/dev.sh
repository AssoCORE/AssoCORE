#!/usr/bin/env bash

# ==============================================================================
# AssoCORE Backend Development Script
# ==============================================================================
# Quick start for backend development with hot-reload:
# - Starts infrastructure services (DB, Redis, Nextcloud) if not running
# - Starts API in development mode with code hot-reload
# - Mounts source code as volume for instant changes
#
# This script is optimized for daily development workflow.
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
    local max_wait=${3:-60}
    local elapsed=0

    while ! eval "$check_command" >/dev/null 2>&1; do
        if [ $elapsed -ge $max_wait ]; then
            print_error "Timeout waiting for $service after ${max_wait}s"
            return 1
        fi

        echo -ne "${YELLOW}⏳${NC} Waiting for $service... ${elapsed}s / ${max_wait}s\r"
        sleep 2
        elapsed=$((elapsed + 2))
    done

    echo -e "\r${GREEN}✓${NC} $service is ready! (${elapsed}s)                    "
    return 0
}

# ==============================================================================
# Main Script
# ==============================================================================

print_header "🚀 AssoCORE Backend Development"

# ------------------------------------------------------------------------------
# Step 1: Prerequisites
# ------------------------------------------------------------------------------
print_step "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null || ! docker info &> /dev/null; then
    print_error "Docker is not available or not running"
    exit 1
fi
print_success "Docker ready"

# Check .env
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo ""
    echo "Please run setup first:"
    echo "  ${YELLOW}./setup.sh${NC}"
    exit 1
fi
print_success ".env file found"

# ------------------------------------------------------------------------------
# Step 2: Check Infrastructure Services
# ------------------------------------------------------------------------------
echo ""
print_step "Checking infrastructure services..."

# Get running services
RUNNING_SERVICES=$(docker compose ps --services --filter "status=running" 2>/dev/null || echo "")

start_infrastructure=false

# Check if key services are running
if ! echo "$RUNNING_SERVICES" | grep -q "db"; then
    print_warning "Database not running"
    start_infrastructure=true
fi

if ! echo "$RUNNING_SERVICES" | grep -q "redis"; then
    print_warning "Redis not running"
    start_infrastructure=true
fi

if ! echo "$RUNNING_SERVICES" | grep -q "nextcloud"; then
    print_warning "Nextcloud not running"
    start_infrastructure=true
fi

# ------------------------------------------------------------------------------
# Step 3: Start Infrastructure if Needed
# ------------------------------------------------------------------------------
if [ "$start_infrastructure" = true ]; then
    echo ""
    print_header "🚢 Starting Infrastructure"

    print_step "Starting database, Redis, and Nextcloud..."
    docker compose up -d db redis nextcloud --remove-orphans

    # Wait for services
    echo ""
    DB_CONTAINER=$(docker compose ps -q db)
    wait_for_service "MariaDB" \
        "docker exec $DB_CONTAINER mariadb-admin ping -h localhost --silent" \
        90 || exit 1

    REDIS_CONTAINER=$(docker compose ps -q redis)
    wait_for_service "Redis" \
        "docker exec $REDIS_CONTAINER redis-cli ping | grep -q PONG" \
        30 || exit 1

    NEXTCLOUD_CONTAINER=$(docker compose ps -q nextcloud)
    wait_for_service "Nextcloud" \
        "docker exec $NEXTCLOUD_CONTAINER curl -sf http://localhost:80/status.php" \
        120 || print_warning "Nextcloud might still be starting (continuing anyway)"

    print_success "Infrastructure services ready"
else
    print_success "Infrastructure services already running"
fi

# ------------------------------------------------------------------------------
# Step 4: Stop Production API if Running
# ------------------------------------------------------------------------------
echo ""
if echo "$RUNNING_SERVICES" | grep -q "^api$"; then
    print_step "Stopping production API..."
    docker compose stop api 2>/dev/null || true
    print_success "Production API stopped"
fi

# ------------------------------------------------------------------------------
# Step 5: Start Development API
# ------------------------------------------------------------------------------
echo ""
print_header "💻 Starting Development API"

echo -e "${GREEN}Features:${NC}"
echo "  • Hot-reload enabled (code changes apply instantly)"
echo "  • Source code mounted as volume"
echo "  • Detailed logging"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Access Points:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  🔌 API:         ${GREEN}http://localhost:8000${NC}"
echo -e "  📚 API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  🔍 Redoc:       ${GREEN}http://localhost:8000/redoc${NC}"
echo -e "  🌐 Nextcloud:   ${GREEN}http://localhost:8081${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} Press Ctrl+C to stop the API"
echo ""

# Start API in development mode (with logs following)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up api-dev
