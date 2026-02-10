---
title: DevOps & Infrastructure
description: DevOps practices and infrastructure setup
---

AssoCORE uses modern DevOps practices with Docker, Kubernetes, and GitHub Actions for reliable, scalable deployments.

## Containerization with Docker

### Development Environment

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install

COPY . .

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0"]
```

### Production Build

```dockerfile
# Multi-stage build for optimized images
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry export -f requirements.txt > requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Local Development)

```yaml
version: '3.8'

services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/assocore
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: assocore
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Kubernetes Orchestration

### Deployment Configuration

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: assocore-api
  labels:
    app: assocore-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: assocore-api
  template:
    metadata:
      labels:
        app: assocore-api
    spec:
      containers:
      - name: api
        image: ghcr.io/assocore/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: assocore-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service Configuration

```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: assocore-api
spec:
  selector:
    app: assocore-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Horizontal Pod Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: assocore-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: assocore-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## CI/CD with GitHub Actions

### Pull Request Workflow

```yaml
# .github/workflows/pr.yml
name: Pull Request Checks

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run linters
      run: |
        poetry run ruff check .
        poetry run black --check .
        poetry run mypy .
    
    - name: Run tests
      run: poetry run pytest --cov=app tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
```

### Build & Deploy Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        push: true
        tags: ghcr.io/assocore/api:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=./kubeconfig
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/assocore-api \
          api=ghcr.io/assocore/api:latest
        kubectl rollout status deployment/assocore-api
```

## Deployment Environments

### Development

- Auto-deployed from `develop` branch
- Testing and validation environment
- Lower resource limits

### Staging

- Pre-production environment
- Production-like configuration
- Final validation before release

### Production

- Deployed from `main` branch
- High availability setup
- Multiple replicas across zones

## Monitoring & Observability

### Health Checks

- `/health` - Liveness probe
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

### Logging

- Structured JSON logging
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics

- Request latency
- Error rates
- Resource utilization
- Custom business metrics

## Security

- Secrets management with Kubernetes Secrets
- Image scanning in CI pipeline
- Network policies
- RBAC (Role-Based Access Control)
- Regular security updates
- Signed container images

## Disaster Recovery

- Automated backups
- Multi-region deployment (future)
- Database replication
- Rollback procedures
- Incident response plan
