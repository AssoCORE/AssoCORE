---
title: Technology Stack
description: Technologies and tools used in AssoCORE
---

AssoCORE is built with modern, scalable technologies chosen for their performance, developer experience, and community support.

## Backend

### FastAPI

Our API layer is built with [FastAPI](https://fastapi.tiangolo.com/), a modern Python web framework.

**Why FastAPI?**

- High performance (comparable to NodeJS and Go)
- Built-in data validation with Pydantic
- Automatic API documentation (OpenAPI/Swagger)
- Native async/await support
- Type hints for better code quality and IDE support

**Key Features:**

- RESTful API endpoints
- Automatic request/response validation
- Built-in authentication and authorization
- WebSocket support for real-time features
- Dependency injection system

## DevOps & Infrastructure

### Docker

Application containerization for consistent deployments across environments.

**Usage:**

- Development environment setup
- Production deployment containers
- Service isolation and management
- Multi-stage builds for optimized images

### Kubernetes

Container orchestration for scalable, resilient deployments.

**Features:**

- Auto-scaling based on load
- Self-healing containers
- Zero-downtime deployments
- Service discovery and load balancing
- Configuration and secret management

### GitHub Actions

CI/CD pipeline automation for continuous integration and deployment.

**Workflows:**

- Automated testing on pull requests
- Code quality checks and linting
- Docker image building and publishing
- Automated deployment to Kubernetes
- Security scanning

## Development Tools

### Python Ecosystem

- **Poetry/pip** - Dependency management
- **pytest** - Testing framework
- **Black** - Code formatting
- **mypy** - Static type checking
- **Ruff** - Fast Python linter

## Infrastructure Architecture

```schema
┌─────────────────┐
│  GitHub Actions │ ──► CI/CD Pipeline
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Docker Images  │ ──► Container Registry
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Kubernetes    │ ──► Orchestration
│   ┌─────────┐   │
│   │ FastAPI │   │ ──► Backend API
│   └─────────┘   │
└─────────────────┘
```

## Future Considerations

As AssoCORE grows, we're evaluating:

- Message queue systems (RabbitMQ, Redis)
- Caching layers
- Monitoring and observability tools
- Database solutions (PostgreSQL, MongoDB)
- CDN for static assets
