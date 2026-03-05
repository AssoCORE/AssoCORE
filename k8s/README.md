# Kubernetes Infrastructure for AssoCORE

This directory contains Kubernetes manifests for deploying AssoCORE to a Kubernetes cluster.

> **📚 NEW TO KUBERNETES?** Check out our [Complete Kubernetes Deployment Guide](../docs/src/content/docs/guides/how-to/kubernetes-deployment.mdx) with beginner-friendly explanations, examples, and troubleshooting tips!
> **🐳 NEW TO DOCKER?** Start with our [Docker Basics Guide](../docs/src/content/docs/guides/how-to/docker-basics.mdx) first!

## Quick Start (TL;DR)

```bash
# 1. Install k3d cluster (easiest for local development)
./k8s/install-k3d.sh

# 2. Deploy core services (Traefik, Watchtower, Secrets)
./k8s/deploy-core-services.sh YOUR_GITHUB_USERNAME YOUR_GITHUB_TOKEN

# 3. Access Traefik dashboard
kubectl port-forward -n assocore svc/traefik-dashboard 9000:9000
# Open: http://localhost:9000/dashboard/
```

**That's it!** You now have a running Kubernetes cluster with ingress and auto-updates. 🎉

---

## Structure

```txt
k8s/
├── 00-namespace/          # Namespace configuration
├── 01-secrets/            # Secrets management (GHCR, certificates)
├── 02-traefik/            # Traefik Ingress Controller
├── 03-watchtower/         # Watchtower for automated updates
├── apps/                  # Application deployments (backend, frontend, mobile)
├── ingress/               # Ingress routes configuration
└── deploy-core-services.sh # One-command deployment script
```

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
# http://localhost:3000 (admin/admin)
```

### 3. Manual Deployment (Step-by-Step)

If you prefer to deploy services individually:

```bash
# Step 1: Create namespace
kubectl apply -f k8s/00-namespace/namespace.yaml

# Step 2: Create GHCR secret
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

📖 **See [OBSERVABILITY.md](./OBSERVABILITY.md) for detailed monitoring setup and dashboard configuration.**

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
- [k3s Setup Guide](./K3S_SETUP.md) - Bare metal/production k3s installation
- [Observability Stack](./OBSERVABILITY.md) - **Prometheus + Grafana monitoring and dashboards**

### **🔧 External Resources**

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
