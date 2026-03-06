# New Deployment Issues - March 2026

This document covers three new issues discovered during team deployment testing.

---

## Issue #1: Permission Denied on .zshrc During k3d Installation

### Symptoms

During `./k8s/install-k3d.sh` execution:

```bash
./k8s/install-k3d.sh: line 69: /home/username/.zshrc: Permission denied
```

The cluster installs successfully but `KUBECONFIG` is not added to shell configuration.

### Root Cause

The script tries to append `export KUBECONFIG=~/.kube/config` to `~/.zshrc` but:

- File might be owned by root (common in WSL)
- File might have restrictive permissions
- File might be read-only

### Impact

Medium - k3d cluster works, but `kubectl` won't connect in new terminal sessions.

### Fixed In

✅ [k8s/install-k3d.sh](../k8s/install-k3d.sh) - Commit: [link]

- Added permission checks before writing
- Graceful error handling instead of script failure
- Provides manual instructions if automatic config fails

### Workaround (If Using Old Script)

```bash
# Fix file permissions
sudo chown $USER:$USER ~/.zshrc

# Add KUBECONFIG manually
echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
source ~/.zshrc
```

---

## Issue #2: kubectl Tries to Connect to localhost:8080 (Connection Refused)

### Symptoms

After k3d installation, running any `kubectl` command shows:

```bash
The connection to the server localhost:8080 was refused - did you specify the right host or port?

error: error validating "k8s/00-namespace/namespace.yaml": error validating data: failed to download openapi: Get "http://localhost:8080/openapi/v2?timeout=32s": dial tcp [::1]:8080: connect: connection refused
```

### Root Cause

This is a **consequence of Issue #1**. Because the k3d script couldn't write to `.zshrc`:

1. `KUBECONFIG` environment variable was never set
2. kubectl defaults to `localhost:8080` when no config exists
3. Every kubectl command fails with "connection refused"

### Impact

Critical - Cannot interact with k3d cluster at all.

### Solution

**Immediate fix (current terminal):**

```bash
export KUBECONFIG=~/.kube/config
kubectl get nodes  # Should now work
```

**Permanent fix:**

```bash
echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
source ~/.zshrc
```

**Verification:**

```bash
# Check KUBECONFIG is set
echo $KUBECONFIG
# Should show: /home/username/.kube/config

# Test connection
kubectl cluster-info
kubectl get nodes
```

### Documentation

✅ Created: [docs/KUBECTL_CONNECTION_FIX.md](KUBECTL_CONNECTION_FIX.md)
✅ Updated: [docs/COMMON_ISSUES.md](COMMON_ISSUES.md) - Added as Issue #4
✅ Updated: [k8s/install-k3d.sh](../k8s/install-k3d.sh) - Now detects and warns about this

---

## Issue #3: Backend Deployment Fails (Missing Secrets/Config)

### Symptoms

When running the Backend deployment command:

```bash
kubectl apply -f k8s/09-backend/backend-deployment.yaml
```

**The command fails** with errors about missing secrets or configmaps.

Common error messages:
```bash
error: error validating "k8s/09-backend/backend-deployment.yaml": error validating data: 
  ValidationError(Deployment.spec.template.spec.containers[0].env[0].valueFrom.secretKeyRef): 
  unknown field "backend-db-secret" in io.k8s.api.core.v1.SecretKeySelector
```

Or the deployment is created but pods fail to start:
```bash
kubectl get pods -n assocore
NAME                        READY   STATUS              AGE
backend-xxx                 0/2     CreateContainerConfigError   5m
```

Pod events show:
```bash
kubectl describe pod backend-xxx -n assocore
# Events show:
# Error: secret "backend-db-secret" not found
# Error: secret "ghcr-secret" not found
# Error: configmap "backend-config" not found
```

### Root Cause

**Backend deployment has dependencies that must exist first.**

The backend-deployment.yaml requires:

1. **ghcr-secret** - GitHub Container Registry credentials (for pulling images)
2. **backend-db-secret** - Database connection URL
3. **backend-config** - ConfigMap with environment variables

These must be created **before** applying the deployment.

### Consequence

Because Backend fails to deploy → **Frontend gets stuck in Init:0/1 state**.

The `frontend-deployment.yaml` includes an initContainer that waits for Backend to be available:

```yaml
initContainers:
  - name: wait-for-backend
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nc -z backend.assocore.svc.cluster.local 8000; do
          echo "Waiting for Backend API to be ready..."
          sleep 2
        done
        echo "Backend is ready!"
```

If Backend isn't deployed yet, this initContainer waits forever → Pod never starts.

### Correct Deployment Order

**Step 0: Create all secrets FIRST (Critical!)**

```bash
# This MUST be done before deploying any application
./k8s/01-secrets/create-app-secrets.sh
```

This creates:
- `ghcr-secret` (GitHub Container Registry credentials)
- `backend-db-secret` (Database connection URL)
- `grafana-admin-secret` (Grafana credentials)
- `traefik-dashboard-auth-secret` (Traefik dashboard access)

**Step 1-5: Deploy applications in dependency order:**

1. ✅ **MariaDB** (database)
2. ✅ **Redis** (cache)
3. ✅ **Backend API** ← Depends on: MariaDB, Redis, **secrets**, **backend-config**
4. ✅ **Frontend** ← Depends on: Backend (via initContainer)
5. ✅ **Nextcloud** (independent)

### Solution

**Option 1: Use automated script (recommended):**

```bash
# Assumes secrets are already created
./k8s/deploy-apps.sh
```

The script deploys in correct order automatically.

**Option 2: Manual deployment (follow exact order):**

```bash
# 0. CRITICAL: Create secrets FIRST
./k8s/01-secrets/create-app-secrets.sh

# 1. Database
kubectl apply -f k8s/07-database/mariadb-config.yaml
kubectl apply -f k8s/07-database/mariadb-statefulset.yaml
kubectl wait --for=condition=ready pod/mariadb-0 -n assocore --timeout=300s

# 2. Cache
kubectl apply -f k8s/08-redis/redis-deployment.yaml
kubectl wait --for=condition=available deployment/redis -n assocore --timeout=180s

# 3. Backend (requires secrets + config FIRST)
kubectl apply -f k8s/09-backend/backend-config.yaml     # ← Apply config first!
kubectl apply -f k8s/09-backend/backend-deployment.yaml # ← Then deployment
kubectl wait --for=condition=available deployment/backend -n assocore --timeout=300s

# 4. Frontend (will now find Backend and start successfully)
kubectl apply -f k8s/10-frontend/frontend-deployment.yaml
kubectl wait --for=condition=available deployment/frontend -n assocore --timeout=180s

# 5. Nextcloud
kubectl apply -f k8s/11-nextcloud/nextcloud-config.yaml
kubectl apply -f k8s/11-nextcloud/nextcloud-statefulset.yaml
```

### Debugging

**Check if secrets exist:**

```bash
# List all secrets in namespace
kubectl get secrets -n assocore

# You should see:
# - ghcr-secret
# - backend-db-secret
# - grafana-admin-secret
# - traefik-dashboard-auth-secret
```

**If secrets are missing:**

```bash
# Create them
./k8s/01-secrets/create-app-secrets.sh

# Verify they were created
kubectl get secrets -n assocore
```

**Check if backend-config exists:**

```bash
kubectl get configmap -n assocore | grep backend-config

# If missing, apply it:
kubectl apply -f k8s/09-backend/backend-config.yaml
```

**Check Backend pod status:**

```bash
kubectl get pods -n assocore | grep backend

# If showing CreateContainerConfigError:
kubectl describe pod <backend-pod-name> -n assocore

# Look for events showing missing secrets/configmaps
```

**Check Frontend status (consequence of Backend failure):**

```bash
# View initContainer logs
kubectl logs <frontend-pod-name> -n assocore -c wait-for-backend

# You'll see:
# Waiting for Backend API to be ready...
# (repeating forever because Backend never started)
```

### Impact

High - Backend cannot deploy without secrets → Frontend cannot start → No applications running.

**Cascade effect:**
1. Missing secrets → Backend deployment fails
2. Backend not running → Frontend stuck in Init state
3. No API available → Complete application failure

### Fix

✅ **Must create secrets BEFORE deploying applications:**

```bash
# 1. Ensure .env file is configured
ls -la k8s/.env

# 2. Create all secrets
./k8s/01-secrets/create-app-secrets.sh

# 3. Verify secrets exist
kubectl get secrets -n assocore

# 4. Now deploy applications
./k8s/deploy-apps.sh
```

### Documentation Updated

✅ Updated: [docs/COMMON_ISSUES.md](COMMON_ISSUES.md) - Added as Issue #5
✅ Updated: [docs/src/content/docs/guides/how-to/testing-deployment.mdx](../docs/src/content/docs/guides/how-to/testing-deployment.mdx)

- Added deployment order warning
- Added note about initContainer
- Added debugging tips

---

## Prevention Checklist

To avoid these issues:

- [ ] **After k3d installation**, always verify:

  ```bash
  echo $KUBECONFIG  # Should show path
  kubectl get nodes # Should show cluster nodes
  ```

- [ ] **If KUBECONFIG not set**, add manually:

  ```bash
  echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
  source ~/.zshrc
  ```

- [ ] **CRITICAL: Create secrets BEFORE deploying applications:**

  ```bash
  # Ensure .env file exists and is configured
  ls -la k8s/.env
  
  # Create all secrets
  ./k8s/01-secrets/create-app-secrets.sh
  
  # Verify secrets exist
  kubectl get secrets -n assocore
  ```

- [ ] **Always deploy applications** using the script:

  ```bash
  ./k8s/deploy-apps.sh
  ```

- [ ] **If deploying manually**, follow documented order:
  0. **Create secrets first** (see above)
  1. MariaDB
  2. Redis
  3. Backend config → Backend deployment
  4. Frontend (depends on Backend)
  5. Nextcloud

- [ ] **Check pod status** after each deployment:

  ```bash
  kubectl get pods -n assocore
  ```

---

## Team Communication

**Share with team:**

1. **Updated scripts available** - Pull latest code before deploying:

   ```bash
   git pull origin CI
   ```

2. **Read COMMON_ISSUES.md first** - Covers all known problems

3. **Use automated scripts** - They handle ordering correctly:
   - `./k8s/install-k3d.sh` - Cluster setup
   - `./k8s/deploy-core-services.sh` - Infrastructure
   - `./k8s/deploy-apps.sh` - Applications

4. **If manual deployment**, follow exact order in documentation

5. **If errors occur**, check:
   - [COMMON_ISSUES.md](COMMON_ISSUES.md) - All problems
   - [KUBECTL_CONNECTION_FIX.md](KUBECTL_CONNECTION_FIX.md) - kubectl issues
   - [TRAEFIK_ERRORS_FIX.md](TRAEFIK_ERRORS_FIX.md) - Traefik issues
   - [WATCHTOWER_FIX.md](WATCHTOWER_FIX.md) - Watchtower issues

---

## Summary

| Issue | Severity | Fixed | Workaround |
|-------|----------|-------|------------|
| #1: .zshrc permission denied | Low | ✅ Yes | Add KUBECONFIG manually |
| #2: kubectl localhost:8080 | Critical | ✅ Yes | `export KUBECONFIG=~/.kube/config` |
| #3: Backend deployment fails (missing secrets) | High | ✅ Documented | Create secrets first: `./k8s/01-secrets/create-app-secrets.sh` |

**Root cause of Issue #3:** Backend requires secrets (ghcr-secret, backend-db-secret) and configmap (backend-config) to deploy. If they don't exist, deployment fails with CreateContainerConfigError. This causes Frontend to get stuck waiting for Backend.

All issues now have documentation and fixes/workarounds available.
