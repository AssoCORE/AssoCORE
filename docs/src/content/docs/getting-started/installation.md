---
title: Installation
description: Set up AssoCORE development environment
---

Get AssoCORE up and running on your local machine for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - Usually included with Docker Desktop
- **Git** - [Install Git](https://git-scm.com/downloads/)
- **Poetry** (recommended) - Python dependency management

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

## Clone the Repository

```bash
git clone https://github.com/AssoCORE/AssoCORE.git
cd AssoCORE
```

## Quick Start with Docker

The fastest way to get started is using Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at:

- API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>
- Alternative Docs: <http://localhost:8000/redoc>

## Local Development Setup

For active development, you may prefer running services locally:

### 1. Backend Setup

```bash
cd backend

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Database Setup

Start PostgreSQL with Docker:

```bash
docker run -d \
  --name assocore-db \
  -e POSTGRES_DB=assocore \
  -e POSTGRES_USER=assocore \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 \
  postgres:15-alpine
```

Run database migrations:

```bash
# With Poetry
poetry run alembic upgrade head

# Or directly
alembic upgrade head
```

### 3. Run the API

```bash
# Development mode with hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or
uvicorn app.main:app --reload
```

## Environment Configuration

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://assocore:dev_password@localhost:5432/assocore

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
API_V1_PREFIX=/api/v1
PROJECT_NAME=AssoCORE

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

## Verify Installation

Test the API is working:

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## Development Tools

### Code Formatting

```bash
# Format code with Black
poetry run black .

# Sort imports
poetry run isort .
```

### Linting

```bash
# Run Ruff linter
poetry run ruff check .

# Type checking with mypy
poetry run mypy app/
```

### Testing

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=app tests/

# Run specific test file
poetry run pytest tests/test_users.py
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View database logs
docker logs assocore-db

# Restart database
docker restart assocore-db
```

### Poetry Issues

```bash
# Clear Poetry cache
poetry cache clear . --all

# Reinstall dependencies
rm poetry.lock
poetry install
```

## Next Steps

- [Quick Start Guide](./quickstart.md) - Build your first feature
- [Architecture Overview](../architecture/) - Understand the codebase
- [Contributing Guide](../contributing/) - Make your first contribution

## Need Help?

- Check our [GitHub Issues](https://github.com/AssoCORE/AssoCORE/issues)
- Join our community discussions
- Read the [FAQ](../guides/faq.md)
