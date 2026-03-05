# Common Deployment Issues - Quick Reference

This guide covers the **most common errors** your team will encounter when deploying AssoCORE on k3s/k3d.

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
```
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
```
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

# Verify everything is healthy
kubectl get pods -n assocore
```

**Remember: Secrets FIRST, then deploy services!** 🎯
