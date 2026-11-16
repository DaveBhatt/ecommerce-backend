from http import HTTPStatus

from fastapi import Request #, HTTPException, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder

from app.exceptions.product import ProductNotFoundError, ProductInactiveError, InsufficientStockError
from app.exceptions.cart import CartNotFoundError, CartItemNotFoundError
from app.exceptions.order import OrderNotFoundError, EmptyCartError, InvalidOrderStatusTransitionError

from app.core.logging import logger

def create_problem_response(
        request: Request,
        status_code: int,
        code: str,
        detail: str,
        errors: list[dict] | None = None,
    ) -> JSONResponse:

    """
    Helper function to create a standardized RFC 9457 Problem Details response.
    Application-specific fields such as 'code' and 'errors' are extension members
    supported by RFC 9457.
    """
    try:
        title = HTTPStatus(status_code).phrase
    except ValueError:
        title = "HTTP Error"

    problem = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
    }

    if errors is not None:
        problem["errors"] = errors

    return JSONResponse(
        status_code=status_code,
        content=problem,

        media_type="application/problem+json",
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException,) -> JSONResponse:

    detail = (
        exc.detail
        if isinstance(exc.detail, str)
        else "The request could not be processed."
    )
    return create_problem_response(
        request=request,
        status_code=exc.status_code,
        code="HTTP_ERROR",
        detail=detail,
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError,) -> JSONResponse:
     # Do not expose submitted input input values or internal validation context.
     safe_errors = [
         {
             "location": error["loc"],
             "message": error["msg"],
             "type": error["type"],
         }
         for error in exc.errors()
     ]
     return create_problem_response(
             request=request,
             status_code=422,
             code="VALIDATION_ERROR",
             detail="Request validation failed.",
             errors=safe_errors
         )


async def general_exception_handler(request: Request, exc: Exception,) -> JSONResponse:

    logger.exception(
        "Unhandled exception while processing %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    return create_problem_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        detail="An unexpected error occurred.",
    )


async def product_not_found_handler(request: Request, exc: ProductNotFoundError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=404,
            code="PRODUCT_NOT_FOUND",
            detail="Product not found.",
        )


async def product_inactive_handler(request: Request, exc: ProductInactiveError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=400,
            code="PRODUCT_INACTIVE",
            detail="Product is inactive.",
        )


async def insufficient_stock_handler(request: Request, exc: InsufficientStockError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=400,
            code="INSUFFICIENT_STOCK",
            detail="Insufficient stock available.",
        )

async def cart_not_found_handler(request: Request, exc: CartNotFoundError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=404,
            code="CART_NOT_FOUND",
            detail="Cart not found.",
        )

async def cart_item_not_found_handler(request: Request, exc: CartItemNotFoundError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=404,
            code="CART_ITEM_NOT_FOUND",
            detail="Cart item not found.",
        )

async def order_not_found_handler(request: Request, exc: OrderNotFoundError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=404,
            code="ORDER_NOT_FOUND",
            detail="Order not found.",
        )

async def empty_cart_handler(request: Request, exc: EmptyCartError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=400,
            code="EMPTY_CART",
            detail="Cannot create an order from an empty cart.",
        )

async def invalid_order_status_transition_handler(request: Request, exc: InvalidOrderStatusTransitionError,) -> JSONResponse:

    return create_problem_response(
            request=request,
            status_code=400,
            code="INVALID_ORDER_STATUS_TRANSITION",
            detail="Invalid order status transition.",
        )

