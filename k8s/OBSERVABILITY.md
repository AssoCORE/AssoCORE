# Observability Stack (Prometheus + Grafana)

Self-hosted monitoring and visualization for AssoCORE Kubernetes cluster.

## Overview

This directory contains the complete observability stack:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Pre-configured dashboards**: Kubernetes cluster and pod monitoring

## Quick Start

### Deploy Everything

```bash
# Deploy Prometheus
kubectl apply -f k8s/04-prometheus/

# Deploy Grafana
kubectl apply -f k8s/05-grafana/

# Deploy Ingress Routes
kubectl apply -f k8s/06-ingress/observability-ingress.yaml

# Check status
kubectl get pods -n assocore
```

### Access Services

**Prometheus:**

```bash
# Port forward
kubectl port-forward -n assocore svc/prometheus 9090:9090

# Access at: http://localhost:9090
# OR: http://prometheus.localhost (k3d)
```

**Grafana:**

```bash
# Port forward
kubectl port-forward -n assocore svc/grafana 3000:3000

# Access at: http://localhost:3000
# OR: http://grafana.localhost (k3d)
# Username: admin
# Password: admin (CHANGE THIS!)
```

---

## Prometheus Configuration

### What metrics are collected?

Prometheus scrapes metrics from:

1. **Kubernetes API Server** - Cluster-level metrics
2. **Kubernetes Nodes** - CPU, memory, disk usage
3. **Kubernetes Pods** - Container metrics (CPU, memory, restarts)
4. **Traefik** - HTTP requests, response times, error rates
5. **Prometheus itself** - Internal metrics

### Scrape Configuration

Edit [k8s/04-prometheus/prometheus-config.yaml](../04-prometheus/prometheus-config.yaml):

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['my-app.assocore.svc:8080']
```

Apply changes:

```bash
kubectl apply -f k8s/04-prometheus/prometheus-config.yaml
kubectl rollout restart deployment/prometheus -n assocore
```

### Storage

- **Default retention**: 15 days
- **Storage size**: 10Gi (configurable in deployment.yaml)
- **Location**: PersistentVolume `/prometheus`

To change retention:

```yaml
args:
  - '--storage.tsdb.retention.time=30d'  # 30 days
```

---

## Grafana Configuration

### Pre-installed Dashboards

1. **Kubernetes Cluster Overview**
   - Total nodes, pods, namespaces
   - CPU and memory usage by node
   - Failed pods

2. **Kubernetes Pod Monitoring**
   - CPU usage per pod (AssoCORE namespace)
   - Memory usage per pod
   - Pod restart counts

### Adding Custom Dashboards

#### **Method 1: Via UI**

1. Go to <http://localhost:3000>
2. Click **+** → **Import**
3. Enter dashboard ID or upload JSON
4. Select "Prometheus" as datasource

#### **Method 2: Via ConfigMap**

Edit [k8s/05-grafana/grafana-dashboards.yaml](../05-grafana/grafana-dashboards.yaml):

```yaml
data:
  my-dashboard.json: |
    {
      "dashboard": { ... }
    }
```

Apply:

```bash
kubectl apply -f k8s/05-grafana/grafana-dashboards.yaml
kubectl rollout restart deployment/grafana -n assocore
```

### Popular Dashboard IDs

Import these from grafana.com:

- **3119** - Kubernetes cluster monitoring
- **6417** - Kubernetes pods
- **4701** - JVM (Java apps)
- **11835** - Traefik v2/v3
- **1860** - Node Exporter Full

### Change Admin Password

Edit [k8s/05-grafana/grafana-config.yaml](../05-grafana/grafana-config.yaml):

```bash
# Generate base64 password
echo -n "your-new-password" | base64

# Update secret
kubectl edit secret grafana-admin -n assocore

# Or recreate:
kubectl create secret generic grafana-admin \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=YOUR_NEW_PASSWORD \
  --dry-run=client -o yaml | kubectl apply -f - -n assocore

# Restart Grafana
kubectl rollout restart deployment/grafana -n assocore
```

---

## Troubleshooting

### Prometheus not scraping metrics

```bash
# Check Prometheus logs
kubectl logs -f -n assocore -l app.kubernetes.io/name=prometheus

# Check targets status
# Go to: http://localhost:9090/targets

# Verify RBAC permissions
kubectl describe clusterrole prometheus
```

### Grafana can't connect to Prometheus

```bash
# Check Grafana logs
kubectl logs -f -n assocore -l app.kubernetes.io/name=grafana

# Verify datasource in Grafana
# Settings → Data Sources → Prometheus
# URL should be: http://prometheus.assocore.svc:9090

# Test connectivity from Grafana pod
kubectl exec -it -n assocore deployment/grafana -- /bin/sh
wget -O- http://prometheus.assocore.svc:9090/-/healthy
```

### Dashboards not showing data

1. **Check time range** - Select "Last 1 hour" in Grafana
2. **Verify datasource** - Dashboard settings → Variables
3. **Check Prometheus has data**:

   ```promql
   up
   ```

   Should show targets that are "up"

### Out of disk space

```bash
# Check PVC usage
kubectl get pvc -n assocore

# Reduce retention time (edit deployment)
# OR increase PVC size:
kubectl edit pvc prometheus-storage -n assocore
# Change: storage: 20Gi
```

---

## Query Examples

### PromQL Queries

Test these in Prometheus (<http://localhost:9090/graph>):

**CPU Usage by Pod:**

```promql
rate(container_cpu_usage_seconds_total{namespace="assocore",pod!=""}[5m])
```

**Memory Usage by Pod:**

```promql
container_memory_usage_bytes{namespace="assocore",pod!=""}
```

**HTTP Request Rate (Traefik):**

```promql
rate(traefik_service_requests_total[5m])
```

**Pod Restart Count:**

```promql
kube_pod_container_status_restarts_total{namespace="assocore"}
```

**Available Nodes:**

```promql
count(kube_node_info)
```

**Failed Pods:**

```promql
sum(kube_pod_status_phase{phase=~"Failed|Unknown"})
```

---

## Production Recommendations

### Security

1. **Change default passwords**
   - Grafana admin password
   - Add Prometheus authentication if exposed

2. **Enable TLS**
   - Use cert-manager for automatic certificates
   - Configure Traefik IngressRoute with TLS

3. **Restrict access**
   - Use network policies
   - Configure Grafana OAuth (GitHub, Google, etc.)

### Performance

1. **Tune scrape intervals**

   ```yaml
   global:
     scrape_interval: 30s  # Reduce from 15s if needed
   ```

2. **Increase resources**

   ```yaml
   resources:
     limits:
       cpu: 2000m
       memory: 4Gi
   ```

3. **Add remote write** (long-term storage)

   ```yaml
   remote_write:
     - url: "https://your-long-term-storage.com/api/v1/write"
   ```

### High Availability

1. **Run multiple Prometheus replicas**
   - Use Thanos or Cortex for HA
   - Or use federation

2. **External Grafana database**
   - Use PostgreSQL instead of SQLite
   - Allows multiple Grafana replicas

---

## Cleanup

```bash
# Remove all observability components
kubectl delete -f k8s/06-ingress/observability-ingress.yaml
kubectl delete -f k8s/05-grafana/
kubectl delete -f k8s/04-prometheus/

# Remove PVCs (deletes all data!)
kubectl delete pvc prometheus-storage grafana-storage -n assocore
```

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards Library](https://grafana.com/grafana/dashboards/)
- [Kubernetes Monitoring Guide](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
