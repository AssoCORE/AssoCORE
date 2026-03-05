# Kubernetes Cluster Setup Guide

Setup guide for AssoCORE with full data sovereignty.

## Choose Your Setup

### k3d (Recommended for WSL/Development) ✨

**Perfect for:**
- Windows WSL2 + Docker Desktop
- MacOS development
- Quick setup without systemd
- Localhost port forwarding

**Quick Start:**
```bash
# Ensure Docker is running
docker ps

# Install k3d cluster
./k8s/install-k3d.sh

# Deploy AssoCORE
./k8s/deploy-core-services.sh fenrir42 $GITHUB_TOKEN

# Access on http://localhost and https://localhost
```

**Advantages:**
- ✅ No systemd required
- ✅ 2-minute setup
- ✅ Multi-node in Docker
- ✅ Easy cleanup (`k3d cluster delete assocore`)

---

### k3s Native (Production/Bare Metal)

**Perfect for:**
- Production servers
- VPS/Cloud instances
- Bare metal hardware
- Maximum performance

## Quick Start (Single Node)

Perfect for development or small deployments:

```bash
# Make script executable
chmod +x k8s/install-k3s-single.sh

# Install k3s
./k8s/install-k3s-single.sh

# Verify installation
kubectl get nodes

# Deploy AssoCORE
./k8s/deploy-core-services.sh fenrir42 $GITHUB_TOKEN
```

## Production Setup (High Availability)

For production with multiple nodes and high availability:

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Load Balancer (Optional - HAProxy/Nginx)       │
│  VIP: 192.168.1.100                              │
└─────────────────────────────────────────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
    │                   │             │
┌───▼────────┐   ┌─────▼──────┐  ┌──▼─────────┐
│ Master 1   │   │ Master 2   │  │ Master 3   │
│ 192.168.1.11│  │192.168.1.12│  │192.168.1.13│
└────────────┘   └────────────┘  └────────────┘
              (etcd cluster)
    │                   │             │
    └─────────┬─────────┴─────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
┌───▼────────┐   ┌─────▼──────┐  ┌──▼─────────┐
│ Worker 1   │   │ Worker 2   │  │ Worker 3   │
│ 192.168.1.21│  │192.168.1.22│  │192.168.1.23│
└────────────┘   └────────────┘  └────────────┘
```

### Step 1: Initialize First Master

On the first master node:

```bash
chmod +x k8s/install-k3s-ha.sh
./k8s/install-k3s-ha.sh master-init
```

**Save the output:**
- Master IP: `192.168.1.11`
- Node Token: `K10xxx::server:xxx`

### Step 2: Join Additional Masters (Optional HA)

On each additional master node:

```bash
./k8s/install-k3s-ha.sh master-join 192.168.1.11 K10xxx::server:xxx
```

### Step 3: Join Worker Nodes

On each worker node:

```bash
./k8s/install-k3s-ha.sh worker 192.168.1.11 K10xxx::server:xxx
```

### Step 4: Verify Cluster

From any master node:

```bash
kubectl get nodes
```

Expected output:

```
NAME       STATUS   ROLES                       AGE   VERSION
master-1   Ready    control-plane,etcd,master   5m    v1.28.5+k3s1
master-2   Ready    control-plane,etcd,master   4m    v1.28.5+k3s1
master-3   Ready    control-plane,etcd,master   3m    v1.28.5+k3s1
worker-1   Ready    <none>                      2m    v1.28.5+k3s1
worker-2   Ready    <none>                      1m    v1.28.5+k3s1
```

## Hardware Requirements

### Minimum (Single Node)

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 50 GB SSD
- **OS**: Ubuntu 20.04+, Debian 10+, or any systemd-based Linux

### Recommended (Production HA)

**Master Nodes** (3 nodes):
- CPU: 4 cores
- RAM: 8 GB
- Disk: 100 GB SSD

**Worker Nodes** (3+ nodes):
- CPU: 8 cores
- RAM: 16 GB
- Disk: 200 GB SSD

## k3s Features for Self-Hosted Infrastructure

### Built-in Components

✅ **No External Dependencies**
- Embedded SQLite (single node) or etcd (HA)
- Built-in container runtime (containerd)
- Automatic TLS certificate management

✅ **Lightweight**
- Binary size: ~60 MB
- Memory footprint: ~512 MB
- Fast startup: <30 seconds

✅ **Production Ready**
- CNCF certified Kubernetes
- Same API as full Kubernetes
- Regular security updates

### Disabled Components (We'll Deploy Our Own)

We disabled these because we want more control:
- ❌ Traefik (we deploy our custom Traefik configuration)
- ❌ ServiceLB (we use MetalLB or external LB)

## Network Configuration

### Required Ports

**Master Nodes:**
- `6443`: Kubernetes API server
- `10250`: Kubelet metrics
- `2379-2380`: etcd (HA only)

**Worker Nodes:**
- `10250`: Kubelet metrics

**Allow all traffic:**
- Between all cluster nodes (internal network)

### Firewall Rules (Example with ufw)

```bash
# On all nodes - allow from other cluster nodes
sudo ufw allow from 192.168.1.0/24

# On master nodes - allow API access
sudo ufw allow 6443/tcp

# Enable firewall
sudo ufw enable
```

## Post-Installation Configuration

### 1. Install kubectl (if not installed)

```bash
# k3s provides kubectl as k3s kubectl, but you can install standalone:
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### 2. Setup Kubeconfig Access

```bash
# Already done by install scripts, but if needed:
mkdir -p ~/.kube
sudo cat /etc/rancher/k3s/k3s.yaml > ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config
```

### 3. Deploy MetalLB (for LoadBalancer services)

k3s doesn't include a LoadBalancer implementation. For self-hosted, use MetalLB:

```bash
# Install MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml

# Create IP pool (adjust to your network)
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.200-192.168.1.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
EOF
```

### 4. Deploy AssoCORE Core Services

```bash
cd /home/julien/delivery/EIP/AssoCORE

# Deploy Traefik, Watchtower, and create secrets
./k8s/deploy-core-services.sh fenrir42 $GITHUB_TOKEN

# Check status
kubectl get pods -n assocore
kubectl get svc -n assocore
```

## Cluster Management

### View Logs

```bash
# k3s service logs
sudo journalctl -u k3s -f

# Pod logs
kubectl logs -n assocore -l app.kubernetes.io/name=traefik -f
```

### Restart k3s

```bash
sudo systemctl restart k3s
```

### Upgrade k3s

```bash
# Single node
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.29.0+k3s1" sh -

# HA cluster - upgrade masters first, then workers
```

### Uninstall k3s

```bash
# Master/single node
/usr/local/bin/k3s-uninstall.sh

# Worker node
/usr/local/bin/k3s-agent-uninstall.sh
```

## Troubleshooting

### k3s won't start

```bash
# Check status
sudo systemctl status k3s

# View logs
sudo journalctl -u k3s -n 50

# Check if ports are in use
sudo netstat -tulpn | grep -E '6443|10250'
```

### Node not joining cluster

```bash
# Verify token
sudo cat /var/lib/rancher/k3s/server/node-token

# Check network connectivity
ping <master-ip>
telnet <master-ip> 6443

# Check firewall
sudo ufw status
```

### kubectl connection refused

```bash
# Check kubeconfig
echo $KUBECONFIG
cat ~/.kube/config

# Verify k3s is running
sudo systemctl status k3s

# Check API server
sudo k3s kubectl get nodes
```

## Data Sovereignty Checklist

✅ **Infrastructure Control**
- [ ] All servers physically controlled by your organization
- [ ] No cloud provider dependencies
- [ ] Private network or VPN for inter-node communication

✅ **Data Storage**
- [ ] Persistent volumes on local disks or self-hosted storage
- [ ] Database backups stored on-premises
- [ ] No external object storage (S3, etc.)

✅ **Network Isolation**
- [ ] Cluster nodes on private network
- [ ] Firewall rules limiting external access
- [ ] VPN for remote access

✅ **Compliance**
- [ ] Data resides in required jurisdiction
- [ ] Audit logs enabled and retained
- [ ] Encryption at rest and in transit

## Next Steps

1. **Deploy AssoCORE applications**: See `k8s/apps/` directory
2. **Configure DNS**: Point your domain to Traefik LoadBalancer IP
3. **Setup monitoring**: Prometheus + Grafana
4. **Configure backups**: Velero or custom scripts
5. **Setup CI/CD**: GitHub Actions to deploy to your cluster

## Support & Resources

- k3s Documentation: https://docs.k3s.io/
- k3s GitHub: https://github.com/k3s-io/k3s
- AssoCORE Kubernetes Guide: `k8s/README.md`
