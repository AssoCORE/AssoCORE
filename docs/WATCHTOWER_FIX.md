# Quick Fix: Watchtower CrashLoopBackOff

## The Problem

```bash
watchtower-xxx    0/1     CrashLoopBackOff   3 (21s ago)   69s
# OR
watchtower-xxx    0/1     ContainerCreating  0             5m
```

## Why It Happens

**Watchtower expects Docker**, but **k3s/k3d uses containerd**.

- Watchtower tries to mount `/var/run/docker.sock`
- This socket doesn't exist in k3s/k3d
- Volume mount fails → Pod crashes

## The Fix (Choose One)

### Option 1: Disable Watchtower (Recommended)

Watchtower is **NOT essential** for development:

```bash
# Disable it (scale to 0)
kubectl scale deployment/watchtower --replicas=0 -n assocore

# OR delete it completely
kubectl delete deployment/watchtower -n assocore
```

After this, check all pods are healthy:

```bash
kubectl get pods -n assocore
```

You should see only:
- ✅ traefik (2/2 Running)
- ✅ prometheus (1/1 Running)
- ✅ grafana (1/1 Running)

### Option 2: Already Disabled in Latest Code

If you pull the latest code, Watchtower is **already disabled by default** (`replicas: 0`).

```bash
# Pull latest
git pull

# Redeploy
./k8s/deploy-core-services.sh
```

## What is Watchtower?

Watchtower **automatically updates** Docker container images. It's useful for production but:
- ❌ Not necessary for development
- ❌ Doesn't work with k3s containerd
- ❌ Causes CrashLoopBackOff errors

For development, **manually update images** when needed:

```bash
kubectl rollout restart deployment/<name> -n assocore
```

## Verification

After disabling Watchtower:

```bash
# All pods should be Running
kubectl get pods -n assocore

# Logs should be clean
kubectl logs -n assocore deployment/traefik --tail=20
kubectl logs -n assocore deployment/prometheus --tail=20
kubectl logs -n assocore deployment/grafana --tail=20
```

✅ **No more CrashLoopBackOff!**
