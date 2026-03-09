#!/bin/bash
# AssoCORE Docker Production Build and Test
# Build and test production-optimized Docker images locally
#
# Usage: ./scripts/docker-prod.sh

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
echo -e "${CYAN}║          ${GREEN}AssoCORE Production Build & Test${CYAN}                 ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Build and test optimized production Docker images        ║${NC}"
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
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Error: Docker Compose is not available${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Error: Docker daemon is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

echo ""

# ==============================================================================
# STEP 2: Environment Validation
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 2: Validating Environment${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

ENV_FILE="$SCRIPT_DIR/back/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Error: .env file not found at $ENV_FILE${NC}"
    echo ""
    echo "Please create .env file with production credentials."
    echo "Run ./scripts/docker-dev.sh first or create it manually."
    exit 1
fi

echo -e "${GREEN}✓ .env file exists${NC}"

# Check for production-critical variables
source "$ENV_FILE"

if [ -z "$MARIADB_ROOT_PASSWORD" ]; then
    echo -e "${RED}✗ Error: MARIADB_ROOT_PASSWORD not set${NC}"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ Error: DATABASE_URL not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Required environment variables set${NC}"
echo ""

# ==============================================================================
# STEP 3: Build Production Images
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 3: Building Production Images${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$SCRIPT_DIR"

echo "Select services to build:"
echo ""
echo "  1) All production services"
echo "  2) Backend only"
echo "  3) Frontend only"
echo "  4) Mobile only"
echo "  5) Backend + Frontend"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        SERVICES="backend_prod frontend_prod mobile_prod"
        ;;
    2)
        SERVICES="backend_prod"
        ;;
    3)
        SERVICES="frontend_prod"
        ;;
    4)
        SERVICES="mobile_prod"
        ;;
    5)
        SERVICES="backend_prod frontend_prod"
        ;;
    *)
        echo -e "${RED}Invalid choice. Building all services.${NC}"
        SERVICES="backend_prod frontend_prod mobile_prod"
        ;;
esac

echo ""
echo -e "${BLUE}Building: $SERVICES${NC}"
echo ""

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build images
for service in $SERVICES; do
    echo -e "${YELLOW}Building $service...${NC}"
    docker compose --profile prod build --no-cache $service
    echo -e "${GREEN}✓ $service built${NC}"
    echo ""
done

echo -e "${GREEN}✓ All images built successfully${NC}"
echo ""

# ==============================================================================
# STEP 4: Image Information
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 4: Image Information${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Image Sizes:${NC}"
for service in $SERVICES; do
    IMAGE_ID=$(docker compose --profile prod images -q $service 2>/dev/null || echo "")
    if [ -n "$IMAGE_ID" ]; then
        SIZE=$(docker images $IMAGE_ID --format "{{.Size}}")
        echo "  $service: $SIZE"
    fi
done

echo ""

# ==============================================================================
# STEP 5: Test Production Services
# ==============================================================================

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}STEP 5: Test Production Services${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

read -p "Start production services for testing? [Y/n]: " test
test=${test:-y}

if [[ $test =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Starting production services...${NC}"
    echo ""
    
    # Start in detached mode
    docker compose --profile prod up -d $SERVICES db redis nextcloud
    
    echo ""
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5
    
    # Health checks
    echo ""
    echo -e "${YELLOW}Running health checks...${NC}"
    echo ""
    
    # Check database
    if docker compose ps db | grep -q "Up"; then
        echo -e "${GREEN}✓ Database is running${NC}"
    else
        echo -e "${RED}✗ Database failed to start${NC}"
    fi
    
    # Check backend if built
    if echo "$SERVICES" | grep -q "backend_prod"; then
        sleep 3
        if curl -s http://localhost:8000/health &> /dev/null; then
            echo -e "${GREEN}✓ Backend is responding${NC}"
        else
            echo -e "${YELLOW}⚠ Backend health check failed (may need more time)${NC}"
        fi
    fi
    
    # Check frontend if built
    if echo "$SERVICES" | grep -q "frontend_prod"; then
        sleep 3
        if curl -s http://localhost:3000 &> /dev/null; then
            echo -e "${GREEN}✓ Frontend is responding${NC}"
        else
            echo -e "${YELLOW}⚠ Frontend health check failed (may need more time)${NC}"
        fi
    fi
    
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Production Services Running${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${GREEN}Access URLs:${NC}"
    echo ""
    
    if echo "$SERVICES" | grep -q "frontend_prod"; then
        echo -e "  ${CYAN}Frontend:${NC}  http://localhost:3000"
    fi
    
    if echo "$SERVICES" | grep -q "backend_prod"; then
        echo -e "  ${CYAN}Backend:${NC}   http://localhost:8000"
        echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8000/docs"
    fi
    
    echo -e "  ${CYAN}Nextcloud:${NC} http://localhost:8081"
    
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo ""
    echo "  View logs:      docker compose --profile prod logs -f"
    echo "  Check status:   docker compose --profile prod ps"
    echo "  Stop services:  docker compose --profile prod down"
    echo "  View backend:   docker compose --profile prod logs backend_prod"
    echo "  View frontend:  docker compose --profile prod logs frontend_prod"
    echo ""
    
    # Extract mobile APK if built
    if echo "$SERVICES" | grep -q "mobile_prod"; then
        echo -e "${YELLOW}Mobile APK:${NC}"
        if [ -f "$SCRIPT_DIR/build/mobile/assocore.apk" ]; then
            APK_SIZE=$(du -h "$SCRIPT_DIR/build/mobile/assocore.apk" | cut -f1)
            echo "  Location: build/mobile/assocore.apk"
            echo "  Size: $APK_SIZE"
        else
            echo "  APK will be available at: build/mobile/assocore.apk"
        fi
        echo ""
    fi
    
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Production test environment ready!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo "Press Ctrl+C to exit (services will keep running)"
    echo "Or press Enter to stop services now..."
    read
    
    echo ""
    echo -e "${BLUE}Stopping services...${NC}"
    docker compose --profile prod down
    echo -e "${GREEN}✓ Services stopped${NC}"
else
    echo -e "${YELLOW}Skipping service startup${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Production build complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
