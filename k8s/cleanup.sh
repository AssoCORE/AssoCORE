#!/bin/bash
# AssoCORE Cleanup Script
# This script removes all AssoCORE-related resources
#
# Usage: ./k8s/cleanup.sh [--force]

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
FORCE_MODE=false

# Check for --force flag
if [ "$1" = "--force" ]; then
    FORCE_MODE=true
fi

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${RED}AssoCORE Cleanup Script${CYAN}                        ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  This script will remove all AssoCORE resources           ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if [ "$FORCE_MODE" = false ]; then
    echo -e "${RED}⚠️  WARNING: This will delete all AssoCORE resources!${NC}"
    echo ""
    echo "This includes:"
    echo "  - Kubernetes clusters (k3d/k3s)"
    echo "  - Docker containers"
    echo "  - Configuration files (.env, .deployment-info)"
    echo "  - Kubectl configuration (optional)"
    echo ""

    if ! prompt_yes_no "Are you sure you want to continue?" "n"; then
        echo -e "${GREEN}Cleanup cancelled${NC}"
        exit 0
    fi
    echo ""
fi

echo -e "${BLUE}Starting cleanup...${NC}"
echo ""

# ==============================================================================
# Clean up k3d clusters
# ==============================================================================

if command_exists k3d; then
    echo -e "${YELLOW}Checking for k3d clusters...${NC}"
    K3D_CLUSTERS=$(k3d cluster list -o json 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [ -n "$K3D_CLUSTERS" ]; then
        echo "Found k3d clusters:"
        echo "$K3D_CLUSTERS"
        echo ""

        for cluster in $K3D_CLUSTERS; do
            # Check if cluster name contains 'assocore' or ask for confirmation
            if [[ "$cluster" == *"assocore"* ]] || [[ "$cluster" == *"test"* ]]; then
                echo -e "${BLUE}Deleting k3d cluster: $cluster${NC}"
                k3d cluster delete "$cluster" 2>/dev/null || true
            else
                if [ "$FORCE_MODE" = true ]; then
                    echo -e "${YELLOW}Skipping non-AssoCORE cluster: $cluster${NC}"
                else
                    if prompt_yes_no "Delete k3d cluster '$cluster'?" "n"; then
                        echo -e "${BLUE}Deleting k3d cluster: $cluster${NC}"
                        k3d cluster delete "$cluster" 2>/dev/null || true
                    fi
                fi
            fi
        done
        echo -e "${GREEN}✓ k3d clusters cleaned up${NC}"
    else
        echo -e "${GREEN}✓ No k3d clusters found${NC}"
    fi
else
    echo -e "${YELLOW}⊘ k3d not installed, skipping${NC}"
fi
echo ""

# ==============================================================================
# Clean up k3s
# ==============================================================================

if command_exists k3s; then
    echo -e "${YELLOW}k3s is installed${NC}"

    if [ "$FORCE_MODE" = true ]; then
        echo -e "${YELLOW}Force mode: Deleting namespace only (not uninstalling k3s)${NC}"
        if kubectl get namespace $NAMESPACE &>/dev/null 2>&1; then
            kubectl delete namespace $NAMESPACE --timeout=60s 2>/dev/null || true
            echo -e "${GREEN}✓ Namespace deleted${NC}"
        fi
    else
        if prompt_yes_no "Uninstall k3s completely?" "n"; then
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
else
    echo -e "${YELLOW}⊘ k3s not installed, skipping${NC}"
fi
echo ""

# ==============================================================================
# Clean up Docker containers
# ==============================================================================

if command_exists docker; then
    echo -e "${YELLOW}Checking for AssoCORE Docker containers...${NC}"

    # Stop and remove containers with 'assocore' in name
    ASSOCORE_CONTAINERS=$(docker ps -a --filter "name=assocore" --format "{{.Names}}" 2>/dev/null || echo "")

    if [ -n "$ASSOCORE_CONTAINERS" ]; then
        echo "Found containers:"
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
else
    echo -e "${YELLOW}⊘ Docker not available, skipping${NC}"
fi
echo ""

# ==============================================================================
# Clean up configuration files
# ==============================================================================

echo -e "${YELLOW}Cleaning up configuration files...${NC}"

if [ -f "$SCRIPT_DIR/.env" ]; then
    # Backup before deleting
    BACKUP_FILE="$SCRIPT_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$SCRIPT_DIR/.env" "$BACKUP_FILE"
    rm "$SCRIPT_DIR/.env"
    echo -e "${GREEN}✓ .env removed (backup: $(basename $BACKUP_FILE))${NC}"
fi

if [ -f "$SCRIPT_DIR/.deployment-info" ]; then
    rm "$SCRIPT_DIR/.deployment-info"
    echo -e "${GREEN}✓ .deployment-info removed${NC}"
fi

# Clean up kubeconfig
if [ -f "$HOME/.kube/config" ]; then
    if [ "$FORCE_MODE" = true ]; then
        echo -e "${YELLOW}⊘ Keeping kubectl config (use manual cleanup if needed)${NC}"
    else
        if prompt_yes_no "Remove kubectl config (~/.kube/config)?" "n"; then
            BACKUP_FILE="$HOME/.kube/config.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$HOME/.kube/config" "$BACKUP_FILE"
            rm "$HOME/.kube/config"
            echo -e "${GREEN}✓ kubectl config removed (backup: $BACKUP_FILE)${NC}"
        fi
    fi
fi
echo ""

# ==============================================================================
# Summary
# ==============================================================================

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Cleanup Complete! ✨${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

echo "What was cleaned up:"
echo "  ✓ k3d/k3s clusters removed"
echo "  ✓ Docker containers stopped and removed"
echo "  ✓ Configuration files backed up and removed"
echo ""

echo "Backups created in:"
echo "  - $SCRIPT_DIR/.env.backup.*"
if [ -f "$HOME/.kube/config.backup."* ]; then
    echo "  - ~/.kube/config.backup.*"
fi
echo ""

echo -e "${YELLOW}To deploy again, run:${NC}"
echo "  ./k8s/deploy-all.sh"
echo ""

echo -e "${CYAN}All clean! Ready for a fresh deployment. 🧹${NC}"
echo ""
