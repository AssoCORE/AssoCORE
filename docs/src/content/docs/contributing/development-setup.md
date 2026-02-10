---
title: Development Setup
description: Complete development environment setup guide
---

Comprehensive guide for setting up a complete AssoCORE development environment.

## Development Environment

### Required Tools

1. **Python 3.11+**

   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Poetry** (Dependency Management)

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   poetry --version
   ```

3. **Docker & Docker Compose**

   ```bash
   docker --version
   docker-compose --version
   ```

4. **Git**

   ```bash
   git --version
   ```

### Recommended Tools

- **VS Code** with extensions:
  - Python
  - Pylance
  - Docker
  - GitLens
  - REST Client

- **Postman** or **Insomnia** for API testing

- **pgAdmin** or **DBeaver** for database management

## Project Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/AssoCORE.git
cd AssoCORE

# Add upstream remote
git remote add upstream https://github.com/AssoCORE/AssoCORE.git
```

### 2. Install Dependencies

```bash
cd backend
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your local values
nano .env
```

**Development `.env` example:**

```bash
DATABASE_URL=postgresql://assocore:dev_password@localhost:5432/assocore_dev
SECRET_KEY=dev-secret-key-change-this
DEBUG=True
TESTING=False
LOG_LEVEL=DEBUG
```

### 4. Start Development Database

```bash
# Using Docker Compose
docker-compose up -d db

# Or standalone PostgreSQL
docker run -d \
  --name assocore-dev-db \
  -e POSTGRES_DB=assocore_dev \
  -e POSTGRES_USER=assocore \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### 5. Run Database Migrations

```bash
poetry run alembic upgrade head
```

### 6. Seed Development Data (Optional)

```bash
poetry run python scripts/seed_dev_data.py
```

## Running the Application

### Development Server

```bash
# With hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0

# Or with custom port
poetry run uvicorn app.main:app --reload --port 8001

# With specific log level
poetry run uvicorn app.main:app --reload --log-level debug
```

### Docker Development

```bash
# Start all services
docker-compose up

# Rebuild after changes
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api
```

## Development Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix
git checkout -b fix/bug-description
```

### Code Style

We use multiple tools to maintain code quality:

```bash
# Format code
poetry run black .
poetry run isort .

# Lint
poetry run ruff check .
poetry run ruff check --fix .

# Type checking
poetry run mypy app/

# All checks at once
poetry run pre-commit run --all-files
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_users.py

# Run tests matching pattern
poetry run pytest -k "test_user"

# Run with verbose output
poetry run pytest -vv

# Stop on first failure
poetry run pytest -x
```

### Creating Migrations

```bash
# Auto-generate migration
poetry run alembic revision --autogenerate -m "Add user table"

# Manual migration
poetry run alembic revision -m "Custom migration"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Database Management

### Access Database

```bash
# Using Docker exec
docker exec -it assocore-dev-db psql -U assocore -d assocore_dev

# Common commands
\dt          # List tables
\d users     # Describe table
\q           # Quit
```

### Reset Database

```bash
# Drop and recreate
poetry run alembic downgrade base
poetry run alembic upgrade head

# Or with Docker
docker-compose down -v
docker-compose up -d db
poetry run alembic upgrade head
```

## API Development

### Interactive API Docs

Once the server is running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API endpoint (example)
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Debugging

### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or with ipdb (better interface)
import ipdb; ipdb.set_trace()
```

## Common Issues

### Poetry Lock File Conflicts

```bash
poetry lock --no-update
poetry install
```

### Database Connection Errors

```bash
# Check if DB is running
docker ps | grep postgres

# Check connection
poetry run python -c "from app.db import engine; print(engine)"
```

### Port Already in Use

```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

## Performance Profiling

```bash
# Install profiling tools
poetry add --dev py-spy line-profiler

# Profile with py-spy
py-spy top -- poetry run python -m app.main

# Record profile
py-spy record -o profile.svg -- poetry run python script.py
```

## Documentation

### Building Docs Locally

```bash
cd docs
npm install
npm run dev
```

## CI/CD Testing Locally

### Act (Run GitHub Actions Locally)

```bash
# Install act
brew install act  # macOS
# or follow: https://github.com/nektos/act

# Run PR checks
act pull_request

# Run specific job
act -j test
```

## Next Steps

- Review [Code Guidelines](./code-guidelines.md)
- Check [Architecture Documentation](../architecture/)
- Read [API Design Patterns](../architecture/backend-architecture.md)
