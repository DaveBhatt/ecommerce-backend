from typing import cast
from starlette.types import ExceptionHandler

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.api.v1.router import api_router
from app.database.database import engine
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
    HTTPException,
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
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected", 
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            # "error": str(e),
            "database": "disconnected",
        }
    
    
app.include_router(api_router, prefix="/api/v1",)