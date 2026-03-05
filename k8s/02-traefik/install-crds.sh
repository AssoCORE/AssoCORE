#!/bin/bash
# Install Traefik CRDs (Custom Resource Definitions)
# This script downloads and applies the latest Traefik CRDs

set -e

TRAEFIK_VERSION="v3.0"
CRD_BASE_URL="https://raw.githubusercontent.com/traefik/traefik/${TRAEFIK_VERSION}/docs/content/reference/dynamic-configuration"

echo "Installing Traefik ${TRAEFIK_VERSION} CRDs..."
echo ""

# Download and apply CRDs
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/${TRAEFIK_VERSION}/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml

echo ""
echo "✓ Traefik CRDs installed successfully!"
echo ""
echo "Installed CRDs:"
kubectl get crd | grep traefik

echo ""
echo "Next steps:"
echo "1. Deploy Traefik RBAC: kubectl apply -f k8s/02-traefik/traefik-rbac.yaml"
echo "2. Deploy Traefik Config: kubectl apply -f k8s/02-traefik/traefik-config.yaml"
echo "3. Deploy Traefik: kubectl apply -f k8s/02-traefik/traefik-deployment.yaml"
echo "4. Deploy Traefik Service: kubectl apply -f k8s/02-traefik/traefik-service.yaml"
