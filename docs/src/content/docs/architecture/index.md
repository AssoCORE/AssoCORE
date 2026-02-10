---
title: Architecture
description: Technical architecture and design decisions
---

Understanding the technical architecture behind AssoCORE.

## Overview

AssoCORE is built with a modern, scalable architecture that prioritizes developer experience and user satisfaction. Our stack is carefully chosen to support associations of all sizes, from small community groups to large organizations.

## Core Technologies

- **Backend**: FastAPI (Python) - High-performance async API
- **Containerization**: Docker - Consistent deployment environments
- **Orchestration**: Kubernetes - Scalable container management
- **CI/CD**: GitHub Actions - Automated testing and deployment

## Architecture Documentation

### [Technology Stack](./tech-stack.md)

Comprehensive overview of all technologies, frameworks, and tools used in AssoCORE. Learn why we chose FastAPI, Docker, and Kubernetes, and how they work together.

### [Backend Architecture](./backend-architecture.md)

Deep dive into our FastAPI backend:

- Project structure and organization
- Architectural layers (API, Service, Repository)
- Design patterns and best practices
- Async/await patterns
- Security implementation
- Testing strategies

### [DevOps & Infrastructure](./devops-infrastructure.md)

Our deployment and operations setup:

- Docker containerization
- Kubernetes deployment configurations
- GitHub Actions CI/CD pipelines
- Environment management
- Monitoring and observability
- Disaster recovery

## Key Architectural Principles

### 1. **Separation of Concerns**

Clean separation between API layer, business logic, and data access ensures maintainability and testability.

### 2. **Async First**

Leveraging Python's async/await for non-blocking I/O operations, maximizing throughput and responsiveness.

### 3. **Type Safety**

Strong typing with Python type hints and Pydantic models catches errors early and improves IDE support.

### 4. **API-First Design**

Well-documented, versioned REST APIs with automatic OpenAPI/Swagger documentation.

### 5. **Container-Native**

Docker containers ensure consistency from development to production, simplifying deployment.

### 6. **Infrastructure as Code**

Kubernetes manifests and GitHub Actions workflows are version-controlled alongside application code.

### 7. **Security by Default**

Built-in security features: JWT authentication, password hashing, input validation, and SQL injection prevention.

## System Architecture Overview

```schema
┌──────────────────────────────────────────────────┐
│              GitHub Actions                       │
│         (CI/CD Pipeline)                         │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│         Container Registry                        │
│       (GitHub Container Registry)                │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│          Kubernetes Cluster                       │
│  ┌────────────────────────────────────────────┐ │
│  │         FastAPI Backend                     │ │
│  │  - REST API Endpoints                      │ │
│  │  - Business Logic                          │ │
│  │  - Authentication                          │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                   │
│  ┌────────────▼───────────────────────────────┐ │
│  │         PostgreSQL Database                 │ │
│  │  - Member data                             │ │
│  │  - Association records                     │ │
│  │  - Events & activities                     │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## Next Steps

- Review [Technology Stack](./tech-stack.md) for detailed technology choices
- Understand [Backend Architecture](./backend-architecture.md) before contributing
- Learn about [DevOps Infrastructure](./devops-infrastructure.md) for deployment
