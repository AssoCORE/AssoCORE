# kubectl Connection Issues - Quick Fix

## Problem

When running `kubectl` commands, you get errors like:

```bash
error: error validating "k8s/00-namespace/namespace.yaml": error validating data: failed to download openapi: Get "http://localhost:8080/openapi/v2?timeout=32s": dial tcp [::1]:8080: connect: connection refused

The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

## Root Cause

**kubectl is not configured to connect to your k3d cluster.**

By default, kubectl tries to connect to `localhost:8080` when there's no configuration. The `KUBECONFIG` environment variable wasn't set in your shell.

This usually happens when:
1. The k3d installation script couldn't update your shell config file (permission denied)
2. You opened a new terminal without sourcing the config
3. The KUBECONFIG wasn't exported in the current session

---

## Quick Fixes

### Fix 1: Set KUBECONFIG in Current Session

```bash
# For the current terminal session only
export KUBECONFIG=~/.kube/config

# Verify it works
kubectl cluster-info
kubectl get nodes
```

This is **temporary** - you'll need to run this in each new terminal.

### Fix 2: Add to Shell Profile (Permanent)

Choose your shell:

**For Zsh (most common on Mac/modern Linux):**
```bash
echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
source ~/.zshrc
```

**For Bash:**
```bash
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
source ~/.bashrc
```

**Verify:**
```bash
# Check if KUBECONFIG is set
echo $KUBECONFIG
# Should output: /home/youruser/.kube/config

# Test kubectl
kubectl cluster-info
```

### Fix 3: Fix File Permissions (If Script Failed)

If the k3d script showed "Permission denied" for `.zshrc`:

```bash
# Check file ownership
ls -la ~/.zshrc

# Fix if owned by root
sudo chown $USER:$USER ~/.zshrc

# Retry adding KUBECONFIG
echo 'export KUBECONFIG=~/.kube/config' >> ~/.zshrc
source ~/.zshrc
```

---

## Verification Steps

After applying a fix:

```bash
# 1. Check KUBECONFIG is set
echo $KUBECONFIG
# Expected: /home/youruser/.kube/config

# 2. Test cluster connection
kubectl cluster-info
# Should show k3s cluster info, NOT an error

# 3. List nodes
kubectl get nodes
# Should show k3d-assocore nodes

# 4. Try deploying namespace
kubectl apply -f k8s/00-namespace/namespace.yaml
# Should succeed without errors
```

---

## Why This Happens

The k3d installation script **tries** to add `KUBECONFIG` to your shell config automatically, but it can fail if:

1. **Permission Issues**: 
   - File owned by root
   - File not writable
   - WSL permission issues

2. **New Terminal**:
   - You opened a new terminal before sourcing the config
   - Changes only apply after `source ~/.zshrc`

3. **Wrong Shell**:
   - Script added to `.bashrc` but you're using `zsh`
   - Or vice versa

---

## Prevention

**Always run this after k3d installation:**

```bash
# Immediately after k3d installation
export KUBECONFIG=~/.kube/config
source ~/.zshrc  # or ~/.bashrc

# Test before proceeding
kubectl get nodes
```

Add this to the k3d installation documentation/checklist.

---

## Related Issues

- **Problem**: `Permission denied` when k3d script tries to modify `.zshrc`
  - **Solution**: Fixed in updated `install-k3d.sh` script - now handles permission errors gracefully

- **Problem**: kubectl works in one terminal but not another
  - **Solution**: KUBECONFIG is session-specific. Either add to shell profile or export in each terminal.

---

## See Also

- [k3d Installation Script](../k8s/install-k3d.sh) - Updated with better error handling
- [COMMON_ISSUES.md](COMMON_ISSUES.md) - All deployment issues
- [kubectl Configuration Docs](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)
