# mypy: ignore-errors


from typing import cast
from starlette.types import ExceptionHandler

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.api.v1.router import api_router
from app.database.database import async_engine
from app.exceptions.product import (
    ProductNotFoundError,
    ProductInactiveError,
    InsufficientStockError,
)
from app.exceptions.order import (
    OrderNotFoundError,
    EmptyCartError,
    InvalidOrderStatusTransitionError,
)
from app.exceptions.cart import (
    CartNotFoundError,
    CartItemNotFoundError
)
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    product_not_found_handler,
    product_inactive_handler,
    insufficient_stock_handler,
    cart_not_found_handler,
    cart_item_not_found_handler,
    order_not_found_handler,
    empty_cart_handler,
    invalid_order_status_transition_handler,
)


from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="E-commerce Backend API",
    description="""
    A production-oriented E-commerce Backend API built with Python and FastAPI.

    ## Overview

    This application provides backend functionality for an e-commerce platform,
    including user authentication, product and category management, shopping
    carts, order processing, and inventory management.

    ## Architecture

    - **API Layer:** Handles HTTP requests, validation, and responses.
    - **Service Layer:** Implements business logic and transaction workflows.
    - **Repository Layer:** Handles database access and queries.
    - **Database Layer:** Uses PostgreSQL with SQLAlchemy 2.0 Async ORM.

    ## Authentication

    Protected endpoints require JWT Bearer authentication.

    ## Error Handling

    API errors follow RFC 9457 Problem Details and use the
    `application/problem+json` media type.

    ## API Versioning

    The current API is available under `/api/v1`.
    """,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": (
                "User registration and authentication. "
                "Provides JWT access tokens for protected API endpoints."
            ),
        },
        {
            "name": "Users",
            "description": (
                "Authenticated user operations, including retrieving "
                "the current user's profile."
            ),
        },
        {
            "name": "Products",
            "description": (
                "Product catalog management, including product creation, "
                "retrieval, updates, deletion, and availability."
            ),
        },
        {
            "name": "Categories",
            "description": (
                "Manage product categories and retrieve category information."
            ),
        },
        {
            "name": "Cart",
            "description": (
                "Shopping cart operations, including adding products, "
                "updating quantities, removing items, and clearing the cart."
            ),
        },
        {
            "name": "Orders",
            "description": (
                "Order processing, order history, order retrieval, "
                "and order cancellation."
            ),
        },
    ],
)

app.add_exception_handler(
    InvalidOrderStatusTransitionError,
    invalid_order_status_transition_handler,
)

app.add_exception_handler(
    OrderNotFoundError,
    order_not_found_handler,
)

app.add_exception_handler(
    EmptyCartError,
    empty_cart_handler,
)

app.add_exception_handler(
    CartNotFoundError,
    cart_not_found_handler,
)

app.add_exception_handler(
    ProductNotFoundError,
    product_not_found_handler,
)

app.add_exception_handler(
    ProductInactiveError,
    product_inactive_handler,
)

app.add_exception_handler(
    InsufficientStockError,
    insufficient_stock_handler,
)

app.add_exception_handler(
    CartItemNotFoundError,
    cart_item_not_found_handler,
)

# Register global exception handlers
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce Backend API!"}


@app.get("/health")
async def health():
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected", 
        }
    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }
    
    
app.include_router(api_router, prefix="/api/v1",)