# E-commerce Backend API

A production-oriented e-commerce REST API built with Python and FastAPI.

> 🚧 This project is currently under active development.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic
- JWT Authentication
- Docker / Docker Compose
- pytest

## Architecture

The project follows a layered architecture:

API → Services → Repositories → SQLAlchemy → PostgreSQL

## Implemented Features

### Authentication
- User registration
- Password hashing
- JWT authentication
- Protected routes
- Current-user dependency

### Product Catalog
- Categories
- Products
- CRUD operations
- Slug generation
- Stock management

### Cart
- User-specific carts
- Cart items
- Product relationships
- Stock validation
- Cart totals

### Orders
- Checkout
- Order creation
- Order items
- Order ownership validation
- Order status lifecycle
- Order cancellation
- Inventory restoration
- SQLAlchemy eager loading

## Database

PostgreSQL is used as the primary database.

Alembic is used for database schema migrations.

## Running Locally

```bash
git clone https://github.com/DaveBhatt/ecommerce-backend.git
cd ecommerce_backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt