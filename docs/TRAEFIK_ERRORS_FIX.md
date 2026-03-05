# Traefik Errors - Quick Fix Guide

## Problems Your Team Is Seeing

### Error 1: Middleware Not Found

```sh
middleware "assocore-traefik-dashboard-auth@kubernetescrd" does not exist
```

### Error 2: Let's Encrypt Certificate Failures

```sh
DNS problem: NXDOMAIN looking up A for traefik.assocore.org
Cannot issue for "prometheus.assocore.local": Domain name does not end with a valid public suffix (TLD)
```

### Error 3: Watchtower CrashLoopBackOff

```sh
watchtower-9bf54dc66-xtfmc    0/1     CrashLoopBackOff   3 (21s ago)   69s
# Or stuck in ContainerCreating
```

---

## Root Causes

1. **Secrets not created before Traefik deployment**
   - Traefik expects `traefik-dashboard-auth-secret` to exist
   - Without it, the middleware fails

2. **Let's Encrypt trying to issue certificates for invalid domains**
   - `.local` domains = Not valid public domains
   - `localhost` domains = Not valid public domains
   - `assocore.org` = No DNS records configured
   - **Let's Encrypt ONLY works with real public domains that have DNS**

3. **Watchtower incompatible with k3s/k3d**
   - Watchtower expects Docker socket at `/var/run/docker.sock`
   - k3s/k3d uses **containerd**, not Docker
   - Volume mount fails → Pod crashes or gets stuck in ContainerCreating

---

## Solutions

### Option A: Fix for Local Development (Recommended)

Use HTTP instead of HTTPS to avoid certificate issues:

```bash
# 1. Create secrets first
./k8s/01-secrets/create-app-secrets.sh

# 2. Apply HTTP-only ingress routes
kubectl apply -f k8s/06-ingress/observability-ingress-dev.yaml
kubectl apply -f k8s/02-traefik/traefik-dashboard-dev.yaml

# 3. Restart Traefik
kubectl rollout restart deployment/traefik -n assocore

# 4. Access services via HTTP
# - Prometheus: http://prometheus.localhost
# - Grafana: http://grafana.localhost
# - Traefik Dashboard: http://traefik.localhost/dashboard/
```

### Option C: Disable Watchtower (Recommended)

Watchtower is **not essential** for development and causes issues in k3s:

```bash
# Disable Watchtower (scale to 0 replicas)
kubectl scale deployment/watchtower --replicas=0 -n assocore

# Or delete it completely
kubectl delete deployment/watchtower -n assocore

# Verify all pods are now healthy
kubectl get pods -n assocore
```

### Option D: Fix for Production

If you have a real domain with DNS configured:

```bash
# 1. Configure DNS records pointing to cluster
# Example: traefik.yourdomain.com → your-cluster-ip

# 2. Update domain in ingress files
# Change traefik.assocore.org → traefik.yourdomain.com

# 3. Update email in k8s/02-traefik/traefik-config.yaml
# Change admin@assocore.org → your-email@yourdomain.com

# 4. Test with Let's Encrypt staging first
# In traefik-config.yaml, use staging CA:
# caServer: https://acme-staging-v02.api.letsencrypt.org/directory

# 5. Once working, switch to production CA
```

---

## Verification

After applying fixes:

```bash
# Check Traefik logs (should be no errors)
kubectl logs -n assocore deployment/traefik --tail=50

# Check secrets exist
kubectl get secrets -n assocore | grep -E "(traefik|grafana|mariadb)"

# Test access
curl http://prometheus.localhost
curl http://grafana.localhost
curl http://traefik.localhost/dashboard/
```

---

## Prevention

**Always follow this order:**

1. ✅ Create `k8s/.env` with all credentials
2. ✅ Run `./k8s/01-secrets/create-app-secrets.sh`
3. ✅ Verify secrets: `kubectl get secrets -n assocore`
4. ✅ Deploy core services: `./k8s/deploy-core-services.sh`

**Never deploy Traefik before creating secrets!**

---

## Why Let's Encrypt Fails for Local Domains

Let's Encrypt is a **public** Certificate Authority that validates domain ownership via:

- **DNS challenges** - Checks public DNS records
- **HTTP challenges** - Makes HTTP requests to your domain

It **cannot** issue certificates for:

- ❌ `*.local` domains (private networks only)
- ❌ `localhost` or `*.localhost`
- ❌ Domains without public DNS records
- ❌ Internal/private IP addresses

**For local development:** Use HTTP or self-signed certificates
**For production:** Use real domains with proper DNS configuration

---

## See Also

- [Complete Testing Guide](docs/src/content/docs/guides/how-to/testing-deployment.mdx)
- [Secrets Management Guide](docs/src/content/docs/guides/how-to/secrets-management.mdx)
- [Traefik Documentation](https://doc.traefik.io/)
