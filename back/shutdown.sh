#!/usr/bin/env bash

# ==============================================================================
# AssoCORE Backend Shutdown Script
# ==============================================================================
# Stop backend services with options:
# - Stop containers only (keep data)
# - Stop and remove volumes (clean all data)
# - Interactive mode with confirmation
#
# Usage:
#   ./shutdown.sh              - Interactive mode
#   ./shutdown.sh --clean      - Stop and remove all data (no prompt)
#   ./shutdown.sh --keep-data  - Stop but keep data (no prompt)
# ==============================================================================

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

show_usage() {
    echo -e "${CYAN}AssoCORE Backend Shutdown${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./shutdown.sh              Interactive mode (prompts for options)"
    echo "  ./shutdown.sh --clean      Stop and remove all data"
    echo "  ./shutdown.sh --keep-data  Stop but keep data"
    echo "  ./shutdown.sh --help       Show this help"
    echo ""
    echo -e "${GREEN}Options:${NC}"
    echo "  --clean       Stop containers and delete all volumes (database, Nextcloud data)"
    echo "  --keep-data   Stop containers but preserve all data"
    echo "  --help        Display this help message"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo -e "  ${YELLOW}./shutdown.sh${NC}"
    echo "    Interactive shutdown with prompts"
    echo ""
    echo -e "  ${YELLOW}./shutdown.sh --keep-data${NC}"
    echo "    Quick shutdown preserving all data"
    echo ""
    echo -e "  ${YELLOW}./shutdown.sh --clean${NC}"
    echo "    Complete cleanup (useful before fresh setup)"
}

# ==============================================================================
# Parse Arguments
# ==============================================================================

CLEAN_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_MODE="clean"
            shift
            ;;
        --keep-data)
            CLEAN_MODE="keep"
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
done

# ==============================================================================
# Main Script
# ==============================================================================

print_header "🛑 AssoCORE Backend Shutdown"

# ------------------------------------------------------------------------------
# Check Running Services
# ------------------------------------------------------------------------------
print_step "Checking running services..."

RUNNING_SERVICES=$(docker compose ps --services --filter "status=running" 2>/dev/null || echo "")

if [ -z "$RUNNING_SERVICES" ]; then
    print_warning "No services are currently running"
    echo ""

    if [ -d "data" ]; then
        echo "Data directory exists:"
        echo "  🗄️  Database: $(du -sh data/db 2>/dev/null | cut -f1 || echo 'N/A')"
        echo "  ☁️  Nextcloud: $(du -sh data/nextcloud 2>/dev/null | cut -f1 || echo 'N/A')"
        echo ""

        if [ "$CLEAN_MODE" = "clean" ]; then
            print_step "Deleting data directory..."
            sudo rm -rf data/
            print_success "Data directory deleted"
        elif [ "$CLEAN_MODE" != "keep" ]; then
            read -p "$(echo -e ${YELLOW})> Delete data directory? [y/N]: $(echo -e ${NC})" -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_step "Deleting data directory..."
                sudo rm -rf data/
                print_success "Data directory deleted"
            else
                print_success "Data directory preserved"
            fi
        fi
    fi

    exit 0
fi

echo -e "${GREEN}Running services:${NC}"
echo "$RUNNING_SERVICES" | sed 's/^/  • /'
echo ""

# Show data directory size
if [ -d "data" ]; then
    echo -e "${CYAN}Current data:${NC}"
    echo "  🗄️  Database: $(du -sh data/db 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "  ☁️  Nextcloud: $(du -sh data/nextcloud 2>/dev/null | cut -f1 || echo 'N/A')"
    echo ""
fi

# ------------------------------------------------------------------------------
# Determine Cleanup Mode
# ------------------------------------------------------------------------------
if [ -z "$CLEAN_MODE" ]; then
    echo -e "${YELLOW}Shutdown options:${NC}"
    echo "  1) Stop containers (keep data)"
    echo "  2) Stop containers and delete all data"
    echo ""
    read -p "$(echo -e ${CYAN})> Choose option [1-2]: $(echo -e ${NC})" -n 1 -r OPTION
    echo
    echo ""

    case $OPTION in
        1)
            CLEAN_MODE="keep"
            ;;
        2)
            CLEAN_MODE="clean"
            print_warning "This will DELETE all data!"
            read -p "$(echo -e ${RED})⚠ Are you sure? Type 'yes' to confirm: $(echo -e ${NC})" CONFIRM
            if [ "$CONFIRM" != "yes" ]; then
                echo ""
                print_success "Shutdown cancelled"
                exit 0
            fi
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
fi

# ------------------------------------------------------------------------------
# Stop Services
# ------------------------------------------------------------------------------
echo ""
print_header "🔌 Stopping Services"

if [ "$CLEAN_MODE" = "clean" ]; then
    print_step "Stopping containers and removing volumes..."
    docker compose down -v --remove-orphans
    print_success "Containers stopped and volumes removed"

    if [ -d "data" ]; then
        print_step "Deleting data directory..."
        sudo rm -rf data/
        print_success "Data directory deleted"
    fi
else
    print_step "Stopping containers (preserving data)..."
    docker compose down --remove-orphans
    print_success "Containers stopped"
    print_success "Data preserved in ./data/"
fi

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
print_header "✅ Shutdown Complete"

if [ "$CLEAN_MODE" = "clean" ]; then
    echo -e "${GREEN}✓${NC} All services stopped"
    echo -e "${GREEN}✓${NC} All volumes removed"
    echo -e "${GREEN}✓${NC} All data deleted"
    echo ""
    echo -e "To start fresh: ${YELLOW}./setup.sh${NC}"
else
    echo -e "${GREEN}✓${NC} All services stopped"
    echo -e "${GREEN}✓${NC} Data preserved"
    echo ""
    echo -e "To restart: ${YELLOW}./setup.sh${NC} or ${YELLOW}./dev.sh${NC}"
fi

echo ""
