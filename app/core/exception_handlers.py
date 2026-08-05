from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.exceptions.product import ProductNotFoundError, ProductInactiveError, InsufficientStockError

from app.core.logging import logger


async def http_exception_handler(request: Request, exc: HTTPException,) -> JSONResponse: 
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        }),
    ) 

async def validation_exception_handler(request: Request, exc: RequestValidationError,) -> JSONResponse:
     
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": exc.errors(),
                },
            }
        ),
    )


async def general_exception_handler(request: Request, exc: Exception,) -> JSONResponse:

    logger.exception(
        "Unhandled exception while processing %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
        }),
    )


async def product_not_found_handler(request: Request, exc: ProductNotFoundError,) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": "Product not found.",
                },
            }
        ),
    )


async def product_inactive_handler(request: Request, exc: ProductInactiveError,) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": "PRODUCT_INACTIVE",
                    "message": "Product is inactive.",
                },
            }
        ),
    )


async def insufficient_stock_handler(request: Request, exc: InsufficientStockError,) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": "INSUFFICIENT_STOCK",
                    "message": "Insufficient stock available.",
                },
            }
        ),
    )