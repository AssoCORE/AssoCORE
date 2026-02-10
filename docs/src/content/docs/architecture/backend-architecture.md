---
title: Backend Architecture
description: FastAPI backend architecture and design patterns
---

AssoCORE's backend is built with FastAPI, following modern Python best practices and clean architecture principles.

## Project Structure

```zsh
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Dependency injection
│   │
│   ├── api/                 # API layer
│   │   ├── v1/
│   │   │   ├── endpoints/   # API endpoints
│   │   │   └── router.py    # API router
│   │   └── deps.py          # API dependencies
│   │
│   ├── core/                # Core functionality
│   │   ├── security.py      # Authentication & authorization
│   │   ├── config.py        # Settings
│   │   └── exceptions.py    # Custom exceptions
│   │
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── association.py
│   │   └── ...
│   │
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── association.py
│   │   └── ...
│   │
│   ├── services/            # Business logic
│   │   ├── user_service.py
│   │   ├── association_service.py
│   │   └── ...
│   │
│   └── repositories/        # Data access layer
│       ├── user_repository.py
│       └── ...
│
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── alembic/                 # Database migrations
├── Dockerfile
├── pyproject.toml           # Dependencies
└── README.md
```

## Architectural Layers

### 1. API Layer (`api/`)

FastAPI routers and endpoints handling HTTP requests.

**Responsibilities:**

- Request/response handling
- Input validation (via Pydantic)
- HTTP status codes
- API documentation

### 2. Service Layer (`services/`)

Business logic and application workflows.

**Responsibilities:**

- Business rules enforcement
- Complex operations coordination
- Service-to-service communication
- Transaction management

### 3. Repository Layer (`repositories/`)

Data access abstraction.

**Responsibilities:**

- Database queries
- CRUD operations
- Data persistence
- Query optimization

### 4. Models (`models/`)

Database models and ORM definitions (SQLAlchemy/Tortoise).

### 5. Schemas (`schemas/`)

Pydantic models for request/response validation and serialization.

## Design Patterns

### Dependency Injection

FastAPI's dependency injection system for:

- Database session management
- Authentication
- Service instantiation
- Configuration access

```python
from fastapi import Depends
from app.services import UserService

def get_user_service() -> UserService:
    return UserService()

@router.get("/users")
async def list_users(
    service: UserService = Depends(get_user_service)
):
    return await service.list_users()
```

### Repository Pattern

Separating data access logic from business logic.

### Service Pattern

Encapsulating business logic in service classes.

## Key Features

### Async/Await

Non-blocking I/O for better performance:

```python
@router.get("/associations")
async def get_associations():
    async with database.session() as session:
        return await association_service.get_all(session)
```

### Request Validation

Automatic validation with Pydantic:

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    name: str

@router.post("/users")
async def create_user(user: UserCreate):
    # user is already validated
    return await user_service.create(user)
```

### API Documentation

Auto-generated OpenAPI (Swagger) docs at `/docs` and `/redoc`.

### Error Handling

Centralized exception handling with custom exceptions.

## Security

- JWT-based authentication
- Password hashing (bcrypt)
- CORS configuration
- Rate limiting
- Input sanitization
- SQL injection prevention (ORM)

## Testing Strategy

- **Unit Tests**: Service and repository logic
- **Integration Tests**: API endpoints
- **E2E Tests**: Full user workflows
- Test coverage target: >80%

## Performance Considerations

- Database connection pooling
- Query optimization and indexing
- Caching strategies
- Async operations for I/O-bound tasks
- Response compression
