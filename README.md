# E-commerce Backend API

A production-oriented REST API for an e-commerce platform, built with Python and FastAPI. This project focuses on backend engineering practices, including layered architecture, asynchronous database operations, authentication, transaction handling, API validation, and automated testing.

> **Project status:** Active development — core e-commerce functionality and API documentation implemented. Production-readiness improvements are ongoing.

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 Async ORM
- **Database Driver:** asyncpg
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Authentication:** JWT Bearer Authentication
- **Password Hashing:** pwdlib
- **Testing:** pytest, HTTPX, AnyIO
- **Containerization:** Docker and Docker Compose
- **API Documentation:** OpenAPI / Swagger UI

## Architecture

The application follows a layered architecture that separates HTTP handling, business logic, and database operations.

```text
Client
  |
  v
FastAPI Routers
  |
  v
Service Layer
  |
  v
Repository Layer
  |
  v
SQLAlchemy Async ORM
  |
  v
PostgreSQL
```

### Project Structure

```text
app/
├── api/
│   └── v1/
├── core/
├── database/
├── dependencies/
├── exceptions/
├── models/
├── repositories/
├── schemas/
├── services/
└── utils/

migrations/
tests/
```

## Implemented Features

### Authentication and Users
- User registration and login
- Secure password hashing
- JWT access-token authentication
- Protected API endpoints
- Current-user dependency
- User-specific resource access

### Product Catalog
- Product CRUD operations
- Category management
- Slug generation
- Product search and filtering
- Price filtering and sorting
- Pagination
- Inventory and stock validation

### Shopping Cart
- User-specific shopping carts
- Add, update, and remove cart items
- Cart quantity validation
- Product stock validation
- Cart totals and product relationships

### Order Management
- Checkout and order creation
- Order items and order summaries
- User-specific order retrieval
- Paginated order history
- Order ownership validation
- Order cancellation
- Inventory restoration on cancellation
- Optimized relationship loading using SQLAlchemy eager loading

### API Design and Error Handling
- Versioned API under `/api/v1`
- Centralized exception handling
- RFC 9457 Problem Details error responses
- `application/problem+json` media type
- Consistent validation and error responses
- Documented error responses in OpenAPI

### API Documentation
- Organized Swagger UI tags
- Endpoint summaries and descriptions
- Request and response schemas
- Schema examples and field descriptions
- Documented authentication requirements
- Documented standard and error responses

### Database and Infrastructure
- PostgreSQL integration using Docker
- SQLAlchemy 2.0 asynchronous database operations
- Alembic database migrations
- UUID-based model identifiers
- Reusable model mixins for UUIDs and timestamps
- Dedicated test database configuration
- Async database sessions and dependency injection

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/DaveBhatt/ecommerce-backend.git
cd ecommerce-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Configure your PostgreSQL connection, database credentials, JWT secret, and other required application settings.

Do not commit your actual `.env` file.

### 5. Start PostgreSQL

```bash
docker compose up -d
```

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Start the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Running Tests

The project uses pytest with asynchronous HTTP clients and a dedicated test database.

Configure `TEST_DATABASE_URL` separately from the development database before running tests.

Run the test suite:

```bash
pytest -v
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

> Integration and business-logic test coverage are being expanded.

## Development Roadmap

### Completed
- [x] Layered architecture and project setup
- [x] PostgreSQL, Docker, and asynchronous SQLAlchemy integration
- [x] Database models and Alembic migrations
- [x] JWT authentication and authorization
- [x] Product, category, cart, and order modules
- [x] Inventory validation and restoration
- [x] Pagination and API validation
- [x] RFC 9457 error handling
- [x] OpenAPI documentation and examples

### In Progress
- [ ] Integration testing and authorization coverage
- [ ] Business-logic testing and coverage improvements

### Planned

**Performance and Background Processing**
- [ ] Redis integration for caching and rate limiting
- [ ] Celery for asynchronous background task processing
- [ ] Redis as a message broker and task-result backend
- [ ] Background tasks for order notifications, emails, and other time-consuming operations
- [ ] Database indexing, query optimization, and connection-pool tuning

**Security and Reliability**
- [ ] Advanced rate limiting and API security hardening
- [ ] Secure secrets and environment configuration
- [ ] Retry mechanisms and failure handling for background tasks
- [ ] Payment gateway integration and payment lifecycle management

**Deployment and DevOps**
- [ ] Containerize the complete application using Docker Compose
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Automated testing and quality checks in CI
- [ ] Production deployment using a cloud platform
- [ ] Environment-specific deployment configuration

**Monitoring and Observability**
- [ ] Structured application logging
- [ ] Application health and readiness checks
- [ ] Metrics and performance monitoring
- [ ] Error tracking and distributed tracing

## Project Goals

The goal is to build a production-oriented e-commerce backend that demonstrates practical Python backend engineering and the ability to design, develop, test, and deploy scalable REST APIs.

Key engineering areas:

- Clean architecture and maintainable code
- Asynchronous programming with Python
- Relational database design and transaction management
- Authentication, authorization, and API security
- REST API design and standardized error handling
- Automated testing and code quality
- Caching and background processing
- Performance optimization and scalability
- Docker-based deployment and CI/CD
- Logging, monitoring, and production observability

The project will progressively incorporate industry-relevant technologies such as **Redis, Celery, Docker, and GitHub Actions** to demonstrate a broader range of backend engineering skills.