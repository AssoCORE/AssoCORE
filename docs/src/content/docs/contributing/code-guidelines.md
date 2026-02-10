---
title: Code Guidelines
description: Coding standards and best practices for AssoCORE
---

Standards and best practices for contributing to AssoCORE's codebase.

## Python Code Style

### PEP 8 and Beyond

We follow [PEP 8](https://pep8.org/) with some extensions:

- **Line length**: 100 characters (not 79)
- **String quotes**: Double quotes preferred
- **Imports**: Organized with isort
- **Formatting**: Black code formatter

### Type Hints

Always use type hints for function signatures:

```python
# ✅ Good
def get_user(user_id: int) -> User:
    return user_service.get(user_id)

async def create_user(user: UserCreate) -> User:
    return await user_service.create(user)

# ❌ Bad
def get_user(user_id):
    return user_service.get(user_id)
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_membership_fee(
    base_fee: float,
    member_type: MemberType,
    discount_code: str | None = None
) -> float:
    """Calculate the final membership fee with discounts applied.
    
    Args:
        base_fee: The base membership fee before discounts
        member_type: Type of membership (student, regular, senior)
        discount_code: Optional promotional discount code
        
    Returns:
        The final calculated fee after all discounts
        
    Raises:
        ValueError: If base_fee is negative
        InvalidDiscountError: If discount_code is invalid
    """
    if base_fee < 0:
        raise ValueError("Base fee cannot be negative")
    
    # Implementation...
    return final_fee
```

## FastAPI Best Practices

### Router Organization

```python
# ✅ Good: Organized by resource
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(service: UserService = Depends(get_user_service)):
    return await service.list_users()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)
```

### Dependency Injection

```python
# Define dependencies clearly
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token."""
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

# Use in endpoints
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### Error Handling

```python
from app.core.exceptions import AssoCoreException

class UserNotFoundError(AssoCoreException):
    """Raised when user is not found."""
    status_code = 404
    detail = "User not found"

# In service layer
@router.get("/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get(user_id)
    if not user:
        raise UserNotFoundError()
    return user
```

## Pydantic Schemas

### Schema Naming

```python
# ✅ Good: Clear naming convention
class UserBase(BaseModel):
    """Shared properties"""
    email: EmailStr
    name: str

class UserCreate(UserBase):
    """Properties to receive on creation"""
    password: str

class UserUpdate(UserBase):
    """Properties to receive on update"""
    email: EmailStr | None = None
    name: str | None = None

class UserInDB(UserBase):
    """Properties stored in database"""
    id: int
    hashed_password: str
    created_at: datetime

class UserResponse(UserBase):
    """Properties to return to client"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Validation

```python
from pydantic import validator, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=18, le=120)
    
    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

## Database & ORM

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Association(Base):
    """Association model."""
    __tablename__ = "associations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    members = relationship("Member", back_populates="association")
    
    def __repr__(self) -> str:
        return f"<Association(id={self.id}, name={self.name})>"
```

### Repository Pattern

```python
from typing import Generic, TypeVar
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> ModelType | None:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    async def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    async def create(self, obj: dict) -> ModelType:
        db_obj = self.model(**obj)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
```

## Testing

### Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, db: Session):
    """Test user creation endpoint."""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "Test User"
    }
    
    # Act
    response = await client.post("/api/v1/users", json=user_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data  # Don't expose password
```

### Fixtures

```python
@pytest.fixture
async def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_send_email(user_service: UserService):
    """Test email sending is called."""
    with patch("app.services.email_service.send_email") as mock_send:
        mock_send.return_value = AsyncMock()
        
        await user_service.send_welcome_email(user_id=1)
        
        mock_send.assert_called_once()
```

## Async/Await

### When to Use Async

```python
# ✅ Good: Async for I/O operations
async def get_users_from_db():
    async with db.session() as session:
        return await session.execute(select(User))

async def call_external_api():
    async with httpx.AsyncClient() as client:
        return await client.get("https://api.example.com")

# ❌ Bad: Not needed for CPU-bound operations
async def calculate_statistics(numbers: list[int]) -> float:
    # This doesn't benefit from async
    return sum(numbers) / len(numbers)
```

## Security

### Password Handling

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Good: Hash passwords
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ❌ Never store plain passwords
```

### SQL Injection Prevention

```python
# ✅ Good: Use ORM or parameterized queries
user = db.query(User).filter(User.email == email).first()

# ❌ Bad: String concatenation
query = f"SELECT * FROM users WHERE email = '{email}'"  # Vulnerable!
```

## Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```txt
feat: add user profile endpoint
fix: resolve database connection timeout
docs: update API documentation
test: add tests for authentication
refactor: simplify user service logic
chore: update dependencies
```

## Code Review Checklist

- [ ] Code follows style guidelines (passes Black, Ruff, mypy)
- [ ] All functions have type hints
- [ ] Complex logic has explanatory comments
- [ ] New features have tests (>80% coverage)
- [ ] API changes are documented
- [ ] No sensitive data in code or logs
- [ ] Error handling is appropriate
- [ ] Database queries are optimized

## Additional Resources

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Python Testing with pytest](https://docs.pytest.org/)
