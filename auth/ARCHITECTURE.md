# Authentication Module Architecture

## Layer Structure

### 1. Models Layer (`auth/models.py`)
- Database models and entity definitions
- SQLAlchemy ORM models
- Database relationships

### 2. Schemas Layer (`auth/schemas.py`) 
- Pydantic models for request/response validation
- Data transfer objects (DTOs)
- Input validation and serialization

### 3. Repository Layer (`auth/repositories/`)
- Data access layer
- Database operations abstraction
- CRUD operations

### 4. Service Layer (`auth/services/`)
- Business logic implementation
- Application services
- Domain logic and rules

### 5. Controller Layer (`auth/routes.py`)
- HTTP request handling
- Route definitions
- Request/response mapping

### 6. Utils Layer (`auth/utils/`)
- Common utilities and helpers
- Password hashing, JWT tokens
- Email sending, OTP generation

## Design Patterns Applied

- **Repository Pattern**: Abstracts data access
- **Service Pattern**: Encapsulates business logic
- **Dependency Injection**: Services depend on repositories
- **Single Responsibility**: Each layer has one concern
- **Interface Segregation**: Small, focused interfaces
