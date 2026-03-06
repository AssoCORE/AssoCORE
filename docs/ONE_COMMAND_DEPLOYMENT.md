# 🚀 AssoCORE One-Command Deployment

This guide shows you how to deploy the entire AssoCORE platform with a single automated script.

---

## Why Use This Script?

| Feature | Automated (`deploy-all.sh`) | Manual Deployment |
|---------|----------------------------|-------------------|
| **Time to deploy** | 5-10 minutes | 20-30 minutes |
| **Complexity** | Beginner-friendly | Requires Kubernetes knowledge |
| **Error-prone** | ❌ No (automated checks) | ✅ Yes (many manual steps) |
| **Password security** | ✅ Auto-generates secure passwords | ⚠️ Manual (may use weak passwords) |
| **Deployment order** | ✅ Guaranteed correct | ⚠️ Easy to get wrong |
| **Secret management** | ✅ Automated | ⚠️ Manual script execution |
| **Best for** | Development, quick demos | Learning, customization |

**TL;DR:** Use automated deployment unless you specifically need manual control.

---

## Quick Start

**Complete deployment in one command:**

```bash
./k8s/deploy-all.sh
```

That's it! The script will guide you through everything with interactive prompts.

---

## What It Does

The `deploy-all.sh` script automates the entire deployment process:

1. ✅ **Offers fresh start option** (clean up existing deployments)
2. ✅ **Checks prerequisites** (kubectl, openssl, Docker if using k3d)
3. ✅ **Detects or installs Kubernetes cluster** (k3s or k3d)
4. ✅ **Prompts for configuration** (passwords, credentials, domains)
5. ✅ **Generates secure passwords** (or lets you provide your own)
6. ✅ **Creates .env file** with all configuration
7. ✅ **Sets up namespace**
8. ✅ **Creates Kubernetes secrets**
9. ✅ **Deploys core services** (Traefik, Prometheus, Grafana)
10. ✅ **Deploys applications** (MariaDB, Redis, Backend, Frontend, Nextcloud)
11. ✅ **Shows access information** and URLs

---

## Prerequisites

### Required Tools

- `kubectl` - Kubernetes CLI
- `openssl` - For password generation
- **For k3d:** Docker must be running
- **For k3s:** sudo access

### System Requirements

- **k3d:** 2 CPU cores, 4GB RAM, Docker installed
- **k3s:** 2 CPU cores, 4GB RAM, Linux system

---

## Interactive Prompts

The script will ask you questions. Here's what to expect:

### 0. Fresh Start (First Prompt)

```
⚠️  Fresh Start Option

Do you want to perform a fresh start?
This will:
  - Delete existing k3d/k3s clusters
  - Stop and remove project-related Docker containers
  - Remove existing configuration files (.env, .deployment-info)
  - Clean up Kubernetes resources

WARNING: This will delete all existing data!

Perform fresh start? [y/N]:
```

**When to use:**
- 🔄 **Yes (y):** When you want to start completely fresh, remove all previous deployments, or fix a broken installation
- ⏩ **No (n, or Enter):** When you want to keep existing resources or this is your first deployment

**What gets cleaned up:**
- All k3d clusters (prompts for confirmation for non-AssoCORE clusters)
- k3s cluster (asks for confirmation)
- Docker containers with "assocore" in the name
- `k8s/.env` file (backed up before deletion)
- `k8s/.deployment-info` file
- `~/.kube/config` (optional, asks for confirmation)

**Safety features:**
- ✅ Backs up `.env` before deleting (saved as `.env.backup.TIMESTAMP`)
- ✅ Backs up kubeconfig before deleting (saved as `config.backup.TIMESTAMP`)
- ✅ Asks for confirmation before deleting non-AssoCORE clusters
- ✅ Defaults to "No" to prevent accidental cleanup

### 1. Cluster Selection

```
Which Kubernetes distribution do you want to use?

  1) k3d (Kubernetes in Docker) - Recommended for development
  2) k3s (Lightweight Kubernetes) - For production/bare-metal
```

**Choose:**
- `1` for local development (requires Docker)
- `2` for production or if you don't have Docker

### 2. Deployment Mode

```
Choose deployment mode:
  1) Development (HTTP, localhost/IP access)
  2) Production (HTTPS, with Let's Encrypt certificates)
```

**Choose:**
- `1` for local development (no SSL)
- `2` for production with real domain and HTTPS

### 3. Credentials

For each service, the script will:

1. **Generate a secure password** (32 characters, cryptographically secure)
2. **Show you the generated password**
3. **Ask if you want to use it or provide your own**

Example:
```
MariaDB password
Generated password: xK4j9mP2nQ8rL5vW7tY1cZ3bN6hF0dS4
Use this generated password? [Y/n]:
```

Press `Enter` to use the generated password, or type `n` to enter your own.

### 4. GitHub Container Registry

You'll need:
- GitHub username
- Personal Access Token (PAT) with `read:packages` permission

**Create a PAT:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: `read:packages`
4. Copy the token

### 5. Domain (Production Only)

If you chose production mode:
```
Enter your domain name (e.g., assocore.org): 
Enter email for Let's Encrypt notifications:
```

Make sure:
- DNS records point to your server
- Ports 80 and 443 are accessible from the internet

---

## Example Run

**Development deployment:**

```bash
./k8s/deploy-all.sh

# When prompted:
# - Fresh start? n (or press Enter if this is your first deployment)
# - Use existing cluster? n (if you want to set up a new one)
# - Choose: 1 (k3d)
# - Cluster name: assocore-dev (or press Enter for default)
# - Deployment mode: 1 (Development)
# - Press Enter to accept all generated passwords
# - Enter GitHub username and token
# - Wait for deployment to complete...

# You'll get output like:
✓ AssoCORE is now running!

📊 Grafana Monitoring Dashboard
   URL: http://localhost/grafana/
   Username: admin
   Password: xK4j9mP2nQ8rL5vW7tY1cZ3bN6hF0dS4

🌐 Frontend Application
   URL: http://localhost/

# ... more access information
```

**Time estimate:** 5-10 minutes depending on your internet connection.

---

**Redeployment (fresh start):**

```bash
./k8s/deploy-all.sh

# When prompted:
# - Fresh start? y ← Type 'y' to clean everything
# (Script removes old clusters, containers, config files)
# - Continue with new deployment as above...
```

**Time estimate:** 7-12 minutes (includes cleanup time).

---

## What Gets Created

### Files Created

- `k8s/.env` - Your configuration (DO NOT commit to Git!)
- `k8s/.deployment-info` - Access URLs and deployment details

### Kubernetes Resources

**Namespace:** `assocore`

**Core Services:**
- Traefik (Ingress Controller)
- Prometheus (Metrics)
- Grafana (Monitoring)

**Applications:**
- MariaDB (Database)
- Redis (Cache)
- Backend API (FastAPI)
- Frontend (Next.js)
- Nextcloud (File Storage)

**Secrets:**
- `ghcr-secret` - GitHub Container Registry credentials
- `backend-db-secret` - Database connection URL
- `grafana-admin-secret` - Grafana credentials
- `traefik-dashboard-auth-secret` - Traefik dashboard credentials

---

## After Deployment

### Check Status

```bash
# View all pods
kubectl get pods -n assocore

# Should show all pods in Running state:
# NAME                        READY   STATUS    AGE
# mariadb-0                   1/1     Running   5m
# redis-xxx                   1/1     Running   5m
# backend-xxx                 1/1     Running   4m
# frontend-xxx                1/1     Running   3m
# nextcloud-0                 1/1     Running   2m
# grafana-xxx                 1/1     Running   6m
# prometheus-xxx              1/1     Running   6m
# traefik-xxx                 1/1     Running   6m
```

### Access Services

All URLs are shown at the end of the script. Check the output or run:

```bash
cat k8s/.deployment-info
```

### View Passwords

```bash
cat k8s/.env
```

**⚠️ Keep this file secure!** It contains all your credentials.

---

## Troubleshooting

### Script Stops with Error

**If you see errors during deployment:**

1. **Read the error message** - Most errors are self-explanatory
2. **Check common issues:** See [docs/COMMON_ISSUES.md](../docs/COMMON_ISSUES.md)
3. **Verify prerequisites:**
   ```bash
   kubectl version
   docker info  # For k3d
   ```

### Cluster Connection Failed

```
Error: Cannot connect to cluster
```

**Fix:**
```bash
export KUBECONFIG=~/.kube/config
./k8s/deploy-all.sh  # Run again
```

See [docs/KUBECTL_CONNECTION_FIX.md](../docs/KUBECTL_CONNECTION_FIX.md) for details.

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n assocore

# If pod is not Running, check logs:
kubectl logs -n assocore <pod-name>

# Check events:
kubectl describe pod -n assocore <pod-name>
```

**Common issues:**
- **CreateContainerConfigError** - Secrets weren't created (script should handle this)
- **Init:0/1** - Frontend waiting for Backend (script handles deployment order)
- **ImagePullBackOff** - GHCR credentials invalid (check your GitHub token)

### Services Not Accessible

**For k3d:**
- URLs use `localhost` - should work immediately
- Check Traefik is running: `kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik`

**For k3s:**
- URLs use your server's IP address
- Check firewall allows ports 80/443
- Verify Traefik service: `kubectl get svc -n kube-system traefik`

**For production:**
- DNS records must point to your server
- Let's Encrypt certificates take 1-2 minutes to issue
- Check certificate status: `kubectl get certificate -n assocore`

---

## Re-running the Script

### Use Existing Cluster

The script detects existing clusters:

```bash
./k8s/deploy-all.sh

# Will show:
✓ Kubernetes cluster already accessible
Use this existing cluster? [Y/n]:
```

Press `Enter` to use it, or `n` to create a new one.

### Use Existing Configuration

If `k8s/.env` exists:

```bash
./k8s/deploy-all.sh

# Will show:
Found existing .env file
<contents>
Use this existing configuration? [Y/n]:
```

Press `Enter` to reuse it, or `n` to reconfigure.

---

## Manual Deployment (Alternative)

If you prefer manual control, follow the step-by-step guide:

**[Complete Testing Guide](../docs/src/content/docs/guides/how-to/testing-deployment.mdx)**

---

## Cleanup

### Automated Cleanup (Recommended)

**Option 1: Use the standalone cleanup script:**

```bash
./k8s/cleanup.sh
```

This will:
- ✅ Delete all k3d/k3s clusters (with confirmation)
- ✅ Stop and remove Docker containers
- ✅ Clean up configuration files (with backups)
- ✅ Optionally remove Kubernetes resources

**For unattended cleanup (no prompts):**

```bash
./k8s/cleanup.sh --force
```

**Option 2: Re-run deployment script with fresh start:**

```bash
./k8s/deploy-all.sh
```

When prompted for "Fresh Start", answer `y`:
```
Perform fresh start? [y/N]: y
```

**Then simply exit the script** (Ctrl+C) after cleanup if you don't want to redeploy.

---

### Manual Cleanup

If you prefer manual control:

**Remove Everything (k3d):**
```bash
k3d cluster delete assocore-dev
```

**Remove Everything (k3s):**
```bash
# Delete namespace (removes all apps)
kubectl delete namespace assocore

# Or uninstall k3s completely:
/usr/local/bin/k3s-uninstall.sh
```

**Keep Cluster, Remove Apps Only:**
```bash
kubectl delete namespace assocore
```

**Clean configuration files:**
```bash
# Backup first!
cp k8s/.env k8s/.env.backup
rm k8s/.env k8s/.deployment-info
```

---

## Security Notes

### Generated Passwords

- Passwords are **32 characters** using `openssl rand -base64`
- Cryptographically secure random generation
- Safe for production use

### .env File Security

**DO:**
- ✅ Keep it out of Git (already in `.gitignore`)
- ✅ Back it up securely (encrypted storage)
- ✅ Restrict file permissions: `chmod 600 k8s/.env`
- ✅ Use a password manager to store credentials

**DON'T:**
- ❌ Commit to version control
- ❌ Share via email or chat
- ❌ Store in public cloud storage unencrypted

### Production Deployment

For production, also consider:
- Change default usernames (admin → something unique)
- Rotate passwords regularly
- Use network policies to restrict pod-to-pod traffic
- Enable audit logging
- Set resource limits on all pods

---

## Getting Help

**Documentation:**
- [Complete Testing Guide](../docs/src/content/docs/guides/how-to/testing-deployment.mdx) - Step-by-step manual deployment
- [Common Issues](../docs/COMMON_ISSUES.md) - Troubleshooting guide
- [kubectl Connection Fix](../docs/KUBECTL_CONNECTION_FIX.md) - Fix connection errors

**Issues Encountered During Testing:**
- [New Issues - March 2026](../docs/NEW_ISSUES_MARCH_2026.md) - Recently discovered problems and fixes

**Check Pod Logs:**
```bash
kubectl logs -n assocore <pod-name>
```

**Get Pod Events:**
```bash
kubectl describe pod -n assocore <pod-name>
```

---

## What's Next?

After successful deployment:

1. **Explore the UI:**
   - Open the Frontend at the URL shown
   - Check Grafana dashboards
   - Browse Traefik dashboard
   - Set up Nextcloud

2. **Customize Configuration:**
   - Add your own dashboards to Grafana
   - Configure alerting
   - Set up backup strategies

3. **Develop:**
   - Backend API is live at `/api/`
   - API docs at `/api/docs`
   - Connect your development environment

4. **Monitor:**
   - Grafana shows metrics from all services
   - Prometheus scrapes metrics automatically
   - Set up alerts for critical services

---

## Summary

```bash
# One command to deploy everything:
./k8s/deploy-all.sh

# Answer a few prompts
# Wait ~5-10 minutes
# Done! 🎉
```

**No manual configuration. No missing steps. No deployment order issues.**

The script handles everything automatically with sensible defaults and secure password generation.

---

**Questions or Issues?**

Check [docs/COMMON_ISSUES.md](../docs/COMMON_ISSUES.md) or open an issue on GitHub.
