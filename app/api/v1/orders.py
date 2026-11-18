from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.order import CreateOrderRequest, OrderResponse, OrderSummaryResponse
from app.schemas.pagination import PaginationParams, PaginatedResponse
from app.services.order_service import order_service
from app.api.responses import COMMON_ERROR_RESPONSES, problem_response

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={
        **COMMON_ERROR_RESPONSES,
        401: problem_response("Authentication required."),
        404: problem_response("Order not found."),
        400: problem_response("The order request could not be processed."),
    },
)
@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description=(
        "Create a new order for the currently authenticated user. "
        "The order is generated from the user's shopping cart using "
        "the supplied order details. Returns the newly created order."
    ),
)
async def create_order(order_data: CreateOrderRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db),):

    return await order_service.create_order(
        db=db,
        user_id=current_user.id,
        order_data=order_data,
    )

@router.get(
    "",
    response_model=PaginatedResponse[OrderSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List the current user's orders",
    description=(
        "Retrieve a paginated list of orders belonging to the currently "
        "authenticated user. Supports pagination through page and size "
        "query parameters. Returns order summaries and pagination metadata."
    ),
)
async def get_orders(pagination: PaginationParams = Depends(), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db),):

    return await order_service.get_user_orders(
        db=db,
        user_id=current_user.id,
        page=pagination.page,
        size=pagination.size,
    )

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an order by ID",
    description=(
        "Retrieve the details of a specific order using its UUID. "
        "Users can only access orders belonging to their own account. "
        "Returns the complete order details if the order exists."
    ),
)
async def get_order(order_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db),):

    return await order_service.get_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )

@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an order",
    description=(
        "Cancel an existing order belonging to the currently authenticated "
        "user. The order must satisfy the application's cancellation rules. "
        "Returns the updated order after successful cancellation."
    ),
)
async def cancel_order(order_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db),):

    return await order_service.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )