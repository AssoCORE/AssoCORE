# Kubernetes Infrastructure for AssoCORE

This directory contains Kubernetes manifests for deploying AssoCORE to a Kubernetes cluster.

> **📚 NEW TO KUBERNETES?** Check out our [Complete Kubernetes Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx) with beginner-friendly explanations, examples, and troubleshooting tips!
> **🐳 NEW TO DOCKER?** Start with our [Docker Basics Guide](../docs/src/content/docs/guides/how-to/docker-basics.mdx) first!

## Quick Start (TL;DR)

```bash
# 1. Install k3d cluster (easiest for local development)
./k8s/install-k3d.sh

# 2. Deploy core services (Traefik, Watchtower, Monitoring)
./k8s/deploy-core-services.sh YOUR_GITHUB_USERNAME YOUR_GITHUB_TOKEN

# 3. Deploy applications (Backend, Frontend, NextCloud)
./k8s/deploy-apps.sh

# 4. Add to /etc/hosts
echo "127.0.0.1 assocore.localhost api.assocore.localhost files.assocore.localhost" | sudo tee -a /etc/hosts

# 5. Access your application
# Open: http://assocore.localhost
```

**That's it!** You now have a fully running AssoCORE platform in Kubernetes! 🎉

---

## Structure

```txt
k8s/
├── 00-namespace/          # Namespace configuration
├── 01-secrets/            # Secrets management (GHCR, certificates)
├── 02-traefik/            # Traefik Ingress Controller
├── 03-watchtower/         # Watchtower for automated updates
├── 04-prometheus/         # Prometheus monitoring
├── 05-grafana/            # Grafana dashboards
├── 06-ingress/            # Ingress routes for observability
├── 07-database/           # MariaDB StatefulSet
├── 08-redis/              # Redis cache
├── 09-backend/            # FastAPI backend application
├── 10-frontend/           # Next.js frontend application
├── 11-nextcloud/          # NextCloud file storage
├── 12-ingress-apps/       # Ingress routes for applications
├── deploy-core-services.sh # Deploy infrastructure (Traefik, monitoring)
└── deploy-apps.sh         # Deploy applications (backend, frontend, etc.)
```

### Important Note: Service Definitions

**Services are embedded in deployment files, not separate.**

Many Kubernetes manifests combine Service and Deployment in a single file:
- `mariadb-statefulset.yaml` → Contains **both** Service and StatefulSet
- `redis-deployment.yaml` → Contains **both** Service and Deployment
- `backend-deployment.yaml` → Contains **both** Service and Deployment
- `frontend-deployment.yaml` → Contains **both** Service and Deployment
- `nextcloud-statefulset.yaml` → Contains **both** Service and StatefulSet

This is intentional - keeping related resources together makes deployment and management easier.

---

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured and connected to your cluster
- GitHub Personal Access Token with `read:packages` scope
- Domain name configured (e.g., `assocore.org`)

## Quick Start

### 1. Deploy Core Services

```bash
# Make scripts executable
chmod +x k8s/**/*.sh

# Deploy everything in one command
./k8s/deploy-core-services.sh <github-username> <github-token>

# Example:
./k8s/deploy-core-services.sh fenrir42 ghp_xxxxxxxxxxxx
```

This will deploy:

- ✅ Namespace (`assocore`)
- ✅ GHCR image pull secret
- ✅ Traefik Ingress Controller with CRDs
- ✅ Traefik TLS termination (Let's Encrypt)
- ✅ Watchtower for automated updates
- ✅ Prometheus monitoring
- ✅ Grafana dashboards

### 2. Access Services

```bash
# Traefik Dashboard
kubectl port-forward -n assocore svc/traefik-dashboard 9000:9000
# http://localhost:9000/dashboard/

# Prometheus
kubectl port-forward -n assocore svc/prometheus 9090:9090
# http://localhost:9090

# Grafana
kubectl port-forward -n assocore svc/grafana 3000:3000
# http://localhost:3000
# Credentials stored in k8s/.env (GRAFANA_ADMIN_USER / GRAFANA_ADMIN_PASSWORD)
```

### 3. Manual Deployment (Step-by-Step)

If you prefer to deploy services individually:

```bash
# Step 1: Create namespace
kubectl apply -f k8s/00-namespace/namespace.yaml

# Step 2: Create application secrets from .env
cp k8s/.env.example k8s/.env
# Edit k8s/.env and set all required credentials
./k8s/01-secrets/create-app-secrets.sh

# Step 3: Create GHCR secret
./k8s/01-secrets/create-ghcr-secret.sh <username> <token>

# Step 3: Install Traefik CRDs
./k8s/02-traefik/install-crds.sh

# Step 4: Deploy Traefik
kubectl apply -f k8s/02-traefik/traefik-rbac.yaml
kubectl apply -f k8s/02-traefik/traefik-config.yaml
kubectl apply -f k8s/02-traefik/traefik-deployment.yaml
kubectl apply -f k8s/02-traefik/traefik-service.yaml
kubectl apply -f k8s/02-traefik/traefik-dashboard.yaml

# Step 5: Deploy Watchtower
kubectl apply -f k8s/03-watchtower/watchtower-deployment.yaml

# Step 6: Deploy Prometheus (Monitoring)
kubectl apply -f k8s/04-prometheus/

# Step 7: Deploy Grafana (Dashboards)
kubectl apply -f k8s/05-grafana/

# Step 8: Deploy Ingress Routes
kubectl apply -f k8s/06-ingress/observability-ingress.yaml
```

📖 **See [Observability & Monitoring Guide](../docs/src/content/docs/guides/how-to/observability-monitoring.mdx) for detailed monitoring setup and dashboard configuration.**

---

## Application Deployment

Once core services are running, deploy the AssoCORE application stack:

### Prerequisites: Configure Secrets

Before deploying applications, you **must** create secrets for database and application credentials:

```bash
# 1. Copy the template
cp k8s/.env.example k8s/.env

# 2. Generate secure passwords
openssl rand -base64 32  # Run multiple times

# 3. Edit k8s/.env with your credentials
nano k8s/.env

# 4. Create Kubernetes secrets
./k8s/01-secrets/create-app-secrets.sh
```

**⚠️ Never commit k8s/.env to version control!**

📖 **See [Secrets Management Guide](../docs/src/content/docs/guides/how-to/secrets-management.mdx) for comprehensive beginner tutorial and [Secrets Technical Reference](../docs/src/content/docs/reference/secrets-technical-reference.mdx) for advanced topics.**

### Quick Application Deployment

```bash
# Deploy all applications in one command
./k8s/deploy-apps.sh
```

This will deploy:

- ✅ **MariaDB** - Database (StatefulSet with 10Gi storage)
- ✅ **Redis** - Cache for NextCloud
- ✅ **Backend API** - FastAPI REST API (2 replicas)
- ✅ **Frontend** - Next.js web application (2 replicas)
- ✅ **NextCloud** - File storage and document management (StatefulSet with 20Gi storage)
- ✅ **Ingress Routes** - HTTP/HTTPS routing for all services

**Access your application:**

- Frontend: <http://assocore.localhost>
- Backend API: <http://api.assocore.localhost>
- NextCloud: <http://files.assocore.localhost>

📖 **See [Application Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-app-deployment.mdx) for detailed application deployment guide, configuration, and troubleshooting.**

### Manual Application Deployment

```bash
# Deploy in dependency order
kubectl apply -f k8s/07-database/    # MariaDB
kubectl apply -f k8s/08-redis/       # Redis
kubectl apply -f k8s/09-backend/     # Backend API
kubectl apply -f k8s/10-frontend/    # Frontend
kubectl apply -f k8s/11-nextcloud/   # NextCloud
kubectl apply -f k8s/12-ingress-apps/ # Ingress routes
```

### Application Architecture

```txt
Frontend (Next.js)  ─┐
                     │
Backend (FastAPI)   ─┼──▶ MariaDB
                     │
NextCloud           ─┴──▶ Redis
```

**Resource Requirements:**

- Total CPU requests: ~1.5 cores
- Total memory requests: ~2GB
- Total storage: ~30GB (10GB MariaDB + 20GB NextCloud)

---

## Configuration

### Traefik Configuration

#### Entry Points

- **web** (`:80`) - HTTP, redirects to HTTPS
- **websecure** (`:443`) - HTTPS with TLS
- **traefik** (`:9000`) - Dashboard and API

#### TLS/Let's Encrypt

Configure your email in `k8s/02-traefik/traefik-config.yaml`:

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@assocore.org  # CHANGE THIS
```

For testing, use Let's Encrypt staging:

```yaml
caServer: https://acme-staging-v02.api.letsencrypt.org/directory
```

#### Dashboard Access

Default credentials: `admin/admin` ⚠️  **CHANGE THIS!**

Generate new password:

```bash
htpasswd -nb admin your-new-password | base64
```

Update in `k8s/02-traefik/traefik-dashboard.yaml`

### Watchtower Configuration

Watchtower monitors containers and automatically updates them when new images are available.

**Configuration options** (in `k8s/03-watchtower/watchtower-deployment.yaml`):

- `WATCHTOWER_POLL_INTERVAL`: Update check interval (default: 300s)
- `WATCHTOWER_LABEL_ENABLE`: Only update labeled containers
- `WATCHTOWER_CLEANUP`: Remove old images after update
- `WATCHTOWER_SCOPE`: Monitor specific namespace

**Enable auto-update for deployments:**

```yaml
metadata:
  labels:
    com.centurylinklabs.watchtower.enable: "true"
```

### GHCR Image Pull Secret

The secret is created automatically by the deployment script, or manually:

```bash
./k8s/01-secrets/create-ghcr-secret.sh <github-username> <github-token>
```

Use in deployments:

```yaml
spec:
  imagePullSecrets:
    - name: ghcr-secret
```

## Accessing Services

### Get LoadBalancer IP

```bash
kubectl get svc traefik -n assocore
```

### Configure DNS

Point your domain to the LoadBalancer external IP:

```txt
A     assocore.org          -> <EXTERNAL-IP>
A     *.assocore.org        -> <EXTERNAL-IP>
```

### Access Dashboard

```http
https://traefik.assocore.org/dashboard/
```

## Monitoring

### Check deployment status

```bash
# All resources
kubectl get all -n assocore

# Traefik pods
kubectl get pods -n assocore -l app.kubernetes.io/name=traefik

# Traefik logs
kubectl logs -n assocore -l app.kubernetes.io/name=traefik -f

# Watchtower logs
kubectl logs -n assocore -l app.kubernetes.io/name=watchtower -f
```

### Check certificates

```bash
# View ACME storage
kubectl exec -n assocore deployment/traefik -- cat /data/acme.json

# Check certificate details
kubectl describe certificate -n assocore
```

## Troubleshooting

### Traefik not starting

```bash
# Check events
kubectl describe pod -n assocore -l app.kubernetes.io/name=traefik

# Check config
kubectl get configmap traefik-config -n assocore -o yaml

# Check RBAC
kubectl get clusterrolebinding traefik
```

### Let's Encrypt rate limits

If testing, use the staging server in `traefik-config.yaml`:

```yaml
caServer: https://acme-staging-v02.api.letsencrypt.org/directory
```

Production limits: 50 certificates per week per domain.

### Watchtower not updating

```bash
# Check logs
kubectl logs -n assocore -l app.kubernetes.io/name=watchtower -f

# Verify RBAC permissions
kubectl auth can-i update deployments --as=system:serviceaccount:assocore:watchtower -n assocore

# Check if containers have the enable label
kubectl get deployment -n assocore -o jsonpath='{.items[*].metadata.labels}'
```

### Image pull errors

```bash
# Verify secret exists
kubectl get secret ghcr-secret -n assocore

# Test secret manually
kubectl create job test-pull --image=ghcr.io/assocore/assocore/backend:latest -n assocore
```

## Security Best Practices

1. **Change default passwords**
   - Traefik dashboard: Update `traefik-dashboard.yaml`

2. **Use network policies**
   - Restrict pod-to-pod communication
   - Only allow necessary ingress/egress

3. **Enable Pod Security Standards**

   ```bash
   kubectl label namespace assocore pod-security.kubernetes.io/enforce=restricted
   ```

4. **Rotate secrets regularly**

   ```bash
   ./k8s/01-secrets/create-ghcr-secret.sh <username> <new-token>
   ```

5. **Monitor certificate expiration**
   - Let's Encrypt certificates auto-renew
   - Check logs for renewal failures

## Clean Up

### Remove all core services

```bash
# Delete all resources in namespace
kubectl delete namespace assocore

# Delete CRDs (optional)
kubectl delete crd $(kubectl get crd | grep traefik | awk '{print $1}')

# Delete cluster role bindings
kubectl delete clusterrolebinding traefik
kubectl delete clusterrole traefik
```

## Related Documentation

### **📖 Essential Guides (Read These First!)**

- [Docker Basics Guide](../docs/src/content/docs/guides/how-to/docker-basics.mdx) - Start here if you're new to Docker
- [Kubernetes Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx) - **Complete beginner's guide** with kubectl commands, troubleshooting, and examples
- [Docker Deployment with GHCR](../docs/src/content/docs/guides/how-to/docker-deployment.mdx) - CI/CD and container registry setup

### **🏗️ Architecture**

- [DevOps Infrastructure](../docs/src/content/docs/architecture/devops-infrastructure.mdx) - High-level overview of our infrastructure
- [K3s Cluster Setup Guide](../docs/src/content/docs/guides/how-to/k3s-cluster-setup.mdx) - Bare metal/production k3s installation (development with k3d)
- [Observability & Monitoring Guide](../docs/src/content/docs/guides/how-to/observability-monitoring.mdx) - **Prometheus + Grafana monitoring and dashboards**

### **🔐 Security & Secrets**

- [Secrets Management Guide](../docs/src/content/docs/guides/how-to/secrets-management.mdx) - **Complete tutorial** on managing passwords and credentials
- [Secrets Technical Reference](../docs/src/content/docs/reference/secrets-technical-reference.mdx) - Advanced secrets management and production recommendations
- [Security Audit Report](../docs/src/content/docs/reference/security-audit.mdx) - Comprehensive hardcoded secrets audit (January 2025)
- [Application Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-app-deployment.mdx) - Complete guide to deploying all AssoCORE services

### **�🔧 External Resources**

- [Traefik Documentation](https://doc.traefik.io/traefik/) - Official Traefik docs
- [Watchtower Documentation](https://containrrr.dev/watchtower/) - Auto-updater docs
- [k3d Documentation](https://k3d.io/) - k3d (k3s in Docker) docs
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) - Quick kubectl reference

---

## Need Help?

1. **First time with Kubernetes?** → Start with the [Kubernetes Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx)
2. **Troubleshooting?** → Check the troubleshooting section in the [Kubernetes Guide](../docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx#troubleshooting)
3. **Docker issues?** → See the [Docker Basics Guide](../docs/src/content/docs/guides/how-to/docker-basics.mdx#troubleshooting)
4. **Still stuck?** → Ask the team or create an issue on GitHub
