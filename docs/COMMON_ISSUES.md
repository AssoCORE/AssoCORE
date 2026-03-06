# Common Deployment Issues - Quick Reference

This guide covers the **most common errors** your team will encounter when deploying AssoCORE on k3s/k3d.

---

## 🚀 Avoid These Issues: Use Automated Deployment

**Want to skip manual configuration and avoid these errors?**

```bash
./k8s/deploy-all.sh
```

This automated script handles:
- ✅ Correct deployment order
- ✅ Secrets creation before deployments
- ✅ Secure password generation
- ✅ Environment configuration
- ✅ All common pitfalls

**📖 [One-Command Deployment Guide](ONE_COMMAND_DEPLOYMENT.md)**

**Still prefer manual deployment?** Continue reading for troubleshooting help.

---

## Issue 1: Watchtower CrashLoopBackOff ⚠️

### Symptoms

```bash
watchtower-xxx    0/1     CrashLoopBackOff   3 (21s ago)   69s
# OR stuck in ContainerCreating
```

### Root Cause

- Watchtower is designed for **Docker**
- k3s/k3d uses **containerd** (not Docker)
- Watchtower tries to mount Docker socket → Volume mount fails → Pod crashes

### Quick Fix

```bash
# Disable Watchtower (it's not essential)
kubectl scale deployment/watchtower --replicas=0 -n assocore
```

**OR** pull the latest code where it's already disabled:

```bash
git pull
./k8s/deploy-core-services.sh
```

✅ **[Full details: WATCHTOWER_FIX.md](WATCHTOWER_FIX.md)**

---

## Issue 2: Traefik Middleware Not Found 🚫

### Symptoms

```sh
middleware "assocore-traefik-dashboard-auth@kubernetescrd" does not exist
```

### Root Cause

Traefik was deployed **before** secrets were created.

### Quick Fix

```bash
# Create secrets FIRST
./k8s/01-secrets/create-app-secrets.sh

# Verify they exist
kubectl get secrets -n assocore

# Restart Traefik
kubectl rollout restart deployment/traefik -n assocore
```

---

## Issue 3: Let's Encrypt Certificate Failures 🔒

### Symptoms

```sh
DNS problem: NXDOMAIN looking up A for traefik.assocore.org
Cannot issue for "prometheus.assocore.local": Domain name does not end with a valid public suffix (TLD)
```

### Root Cause

Let's Encrypt **cannot** issue certificates for:

- ❌ `.local` domains
- ❌ `localhost` domains
- ❌ Domains without public DNS

### Quick Fix (Local Development)

Use **HTTP instead of HTTPS**:

```bash
# Apply HTTP-only ingress routes
kubectl apply -f k8s/06-ingress/observability-ingress-dev.yaml
kubectl apply -f k8s/02-traefik/traefik-dashboard-dev.yaml

# Access via HTTP
curl http://prometheus.localhost
curl http://grafana.localhost
curl http://traefik.localhost/dashboard/
```

✅ **[Full details: TRAEFIK_ERRORS_FIX.md](TRAEFIK_ERRORS_FIX.md)**

---

## Issue 4: kubectl Connection Refused (localhost:8080) 🔌

### Symptoms

```bash
The connection to the server localhost:8080 was refused - did you specify the right host or port?

error validating data: failed to download openapi: Get "http://localhost:8080/openapi/v2?timeout=32s": dial tcp [::1]:8080: connect: connection refused
```

### Root Cause

kubectl is not configured to connect to your k3d cluster. The `KUBECONFIG` environment variable isn't set in your shell.

This happens when:

- k3d installation script couldn't write to `.zshrc` (permission denied)
- You opened a new terminal without sourcing the config
- KUBECONFIG wasn't exported

### Quick Fix

```bash
# For current session (temporary)
export KUBECONFIG=~/.kube/config

# Or add permanently to shell
echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
source ~/.zshrc

# Verify
kubectl cluster-info
kubectl get nodes
```

✅ **[Full details: KUBECTL_CONNECTION_FIX.md](KUBECTL_CONNECTION_FIX.md)**

---

## Issue 5: Frontend Pod Stuck in Init (ContainerCreating) ⏳

### Symptoms

```bash
kubectl get pods -n assocore
NAME                        READY   STATUS              AGE
frontend-xxx                0/1     Init:0/1            5m
# Pod stays in Init state, never becomes Running
```

Also, Backend might fail to deploy with:

```bash
kubectl get pods -n assocore
NAME                        READY   STATUS                       AGE
backend-xxx                 0/2     CreateContainerConfigError   5m
```

### Root Cause

**Most common: Backend deployment fails due to missing secrets.**

The Backend deployment requires these to exist:
- `ghcr-secret` (GitHub Container Registry credentials)
- `backend-db-secret` (Database connection URL)  
- `backend-config` (ConfigMap with environment)

If secrets don't exist, Backend cannot deploy → Frontend's initContainer waits forever for Backend.

**Secondary cause: Wrong deployment order.**

Even if secrets exist, deploying Frontend before Backend causes the same symptom.

**Dependency chain:**

1. **Secrets** ← MUST create first!
2. MariaDB (database) ← Backend needs this
3. Redis (cache) ← Backend needs this
4. **Backend API** ← Frontend needs this
5. **Frontend** ← Depends on Backend
6. Nextcloud ← Independent

### Quick Fix

**Step 1: Ensure secrets exist (CRITICAL!)**

```bash
# Check if secrets exist
kubectl get secrets -n assocore | grep -E 'ghcr-secret|backend-db-secret'

# If missing, create them:
./k8s/01-secrets/create-app-secrets.sh

# Verify they exist
kubectl get secrets -n assocore
```

**Step 2: Deploy in correct order**

```bash
# Deploy database
kubectl apply -f k8s/07-database/mariadb-config.yaml
kubectl apply -f k8s/07-database/mariadb-statefulset.yaml
kubectl wait --for=condition=ready pod/mariadb-0 -n assocore --timeout=300s

# Deploy cache
kubectl apply -f k8s/08-redis/redis-deployment.yaml
kubectl wait --for=condition=available deployment/redis -n assocore --timeout=180s

# Deploy Backend BEFORE Frontend (secrets must exist!)
kubectl apply -f k8s/09-backend/backend-config.yaml
kubectl apply -f k8s/09-backend/backend-deployment.yaml
kubectl wait --for=condition=available deployment/backend -n assocore --timeout=300s

# NOW deploy Frontend (it will find Backend and start)
kubectl apply -f k8s/10-frontend/frontend-deployment.yaml
```

**Or just use the script (handles secrets check + correct order):**

```bash
# Assumes secrets already created
./k8s/deploy-apps.sh
```

### Debugging

**Check if secrets exist:**

```bash
kubectl get secrets -n assocore

# Required secrets:
# - ghcr-secret
# - backend-db-secret
# - grafana-admin-secret
# - traefik-dashboard-auth-secret
```

**Check Backend pod status:**

```bash
kubectl get pods -n assocore | grep backend

# If showing CreateContainerConfigError:
kubectl describe pod <backend-pod-name> -n assocore

# Look for events like:
# Error: secret "backend-db-secret" not found
# Error: secret "ghcr-secret" not found
# Error: configmap "backend-config" not found
```

**Check what Frontend initContainer is waiting for:**

```bash
# See what the frontend is waiting for
kubectl logs -n assocore <frontend-pod-name> -c wait-for-backend

# You'll see:
# Waiting for Backend API to be ready...
# (repeating until Backend is up)
```

**Fix missing secrets:**

```bash
# Ensure .env is configured
ls -la k8s/.env

# Create secrets
./k8s/01-secrets/create-app-secrets.sh

# Verify
kubectl get secrets -n assocore
```

---

## The Golden Rule: Deployment Order 🏆

**Always follow this order:**

```bash
# 1. Setup environment
cp k8s/.env.example k8s/.env
nano k8s/.env  # Add secure passwords

# 2. Create secrets FIRST
./k8s/01-secrets/create-app-secrets.sh

# 3. Verify secrets exist
kubectl get secrets -n assocore

# 4. THEN deploy services
./k8s/deploy-core-services.sh

# 5. Check everything is running
kubectl get pods -n assocore
```

**❌ Never deploy services before creating secrets!**

---

## Quick Health Check

Run these commands to verify deployment:

```bash
# 1. Check all pods are Running (except watchtower at 0/0)
kubectl get pods -n assocore

# Expected:
# traefik-xxx       1/1     Running
# prometheus-xxx    1/1     Running
# grafana-xxx       1/1     Running

# 2. Check secrets exist
kubectl get secrets -n assocore | grep -E "(traefik|grafana|mariadb)"

# Expected:
# traefik-dashboard-auth-secret
# grafana-admin
# mariadb-secret

# 3. Check logs for errors
kubectl logs -n assocore deployment/traefik --tail=50
kubectl logs -n assocore deployment/prometheus --tail=20
kubectl logs -n assocore deployment/grafana --tail=20
```

---

## Production Readiness Checklist ✅

Before going to production:

- [ ] Real domain with DNS configured
- [ ] Update email in `k8s/02-traefik/traefik-config.yaml`
- [ ] Test Let's Encrypt with **staging** CA first
- [ ] Strong passwords in `k8s/.env` (use `openssl rand -base64 32`)
- [ ] Rotate default credentials
- [ ] Backup `.env` file securely
- [ ] Document credentials in password manager
- [ ] Configure monitoring alerts
- [ ] Set up backup strategy

---

## Frequently Asked Questions

### Q: Where are the Service YAML files?

**A:** Services are **embedded** in the same files as their Deployments/StatefulSets, not separate files.

**File structure:**

- `mariadb-statefulset.yaml` → Contains **both** Service and StatefulSet
- `redis-deployment.yaml` → Contains **both** Service and Deployment  
- `backend-deployment.yaml` → Contains **both** Service and Deployment
- `frontend-deployment.yaml` → Contains **both** Service and Deployment
- `nextcloud-statefulset.yaml` → Contains **both** Service and StatefulSet

**This is intentional** - keeping related resources together makes deployment easier.

### Q: Can I deploy applications without core services?

**A:** No! Applications depend on core services:

- Backend needs **Prometheus** for metrics
- All services need **Traefik** for ingress
- Monitoring needs **Grafana** and **Prometheus**

**Always deploy in this order:**

1. ✅ Core services (`./deploy-core-services.sh`)
2. ✅ Applications (`./deploy-apps.sh`)

### Q: What's the difference between deploy-core-services.sh and deploy-apps.sh?

**Core Services** (infrastructure):

- Namespace
- Secrets
- Traefik (Ingress Controller)
- Watchtower (Auto-updater, disabled by default)
- Prometheus (Metrics)
- Grafana (Dashboards)
- Observability ingress routes

**Application Services** (your app):

- MariaDB Database
- Redis Cache
- Backend API (FastAPI)
- Frontend Web (Next.js)
- Nextcloud
- Application ingress routes

---

## Get Help

- **Full Testing Guide**: [testing-deployment.mdx](../src/content/docs/guides/how-to/testing-deployment.mdx)
- **Secrets Management**: [secrets-management.mdx](../src/content/docs/guides/how-to/secrets-management.mdx)
- **Traefik Errors**: [TRAEFIK_ERRORS_FIX.md](TRAEFIK_ERRORS_FIX.md)
- **Watchtower Issue**: [WATCHTOWER_FIX.md](WATCHTOWER_FIX.md)

---

## TL;DR - Most Common Fixes

```bash
# Fix 1: Disable Watchtower (CrashLoopBackOff)
kubectl scale deployment/watchtower --replicas=0 -n assocore

# Fix 2: Create secrets (Middleware not found)
./k8s/01-secrets/create-app-secrets.sh
kubectl rollout restart deployment/traefik -n assocore

# Fix 3: Use HTTP for local dev (Certificate errors)
kubectl apply -f k8s/06-ingress/observability-ingress-dev.yaml
kubectl apply -f k8s/02-traefik/traefik-dashboard-dev.yaml

# Fix 4: kubectl connection refused (localhost:8080)
export KUBECONFIG=~/.kube/config
# Or permanently: echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc && source ~/.zshrc

# Fix 5: Backend deployment fails / Frontend stuck waiting
# CREATE SECRETS FIRST (required for Backend to deploy)
./k8s/01-secrets/create-app-secrets.sh
kubectl get secrets -n assocore  # Verify they exist
# Then deploy apps in correct order:
./k8s/deploy-apps.sh

# Verify everything is healthy
kubectl get pods -n assocore
```

**Remember: Secrets FIRST, then deploy Core Services, then Applications!** 🎯
