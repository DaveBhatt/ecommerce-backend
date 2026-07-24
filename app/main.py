from typing import cast
from starlette.types import ExceptionHandler

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.api.v1.router import api_router
from app.database.database import engine
from app.core.exception_handlers import http_exception_handler, validation_exception_handler, general_exception_handler

from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="E-commerce Backend API",
)

# Register global exception handlers
app.add_exception_handler(
    HTTPException,
    cast(ExceptionHandler, http_exception_handler),
)

app.add_exception_handler(
    RequestValidationError,
    cast(ExceptionHandler, validation_exception_handler),
)

app.add_exception_handler(
    Exception,
    cast(ExceptionHandler, general_exception_handler),
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