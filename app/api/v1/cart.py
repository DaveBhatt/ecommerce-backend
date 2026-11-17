from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.database.session import get_async_db
from app.models.user import User
from app.schemas.cart import CartResponse, AddCartItemRequest, UpdateCartItemRequest
from app.services.cart_service import cart_service
from app.api.responses import COMMON_ERROR_RESPONSES, problem_response


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
    responses={
        **COMMON_ERROR_RESPONSES,
        401: problem_response("Authentication required."),
        404: problem_response("Cart or cart item not found."),
        400: problem_response("The cart request could not be processed."),
    },
)

@router.get("", response_model=CartResponse, status_code=status.HTTP_200_OK,)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession =  Depends(get_async_db),):

    return await cart_service.get_cart(
        db=db,
        user_id=current_user.id,
    )

@router.post("/items", response_model=CartResponse, status_code=status.HTTP_200_OK,)
async def add_item(request: AddCartItemRequest, current_user: User = Depends(get_current_user), db: AsyncSession =  Depends(get_async_db),):

    return await cart_service.add_item(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id,
        quantity=request.quantity,
    )

@router.patch("/items/{cart_item_id}", response_model=CartResponse, status_code=status.HTTP_200_OK,)
async def update_cart_item(cart_item_id: UUID, request: UpdateCartItemRequest, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):

    return await cart_service.update_quantity(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id,
        quantity=request.quantity,
    )

@router.delete("/items/{cart_item_id}", response_model=CartResponse, status_code=status.HTTP_200_OK,)
async def remove_cart_item(cart_item_id: UUID, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):

    return await cart_service.remove_item(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id,
    )

@router.delete("", response_model=CartResponse, status_code=status.HTTP_200_OK,)
async def clear_cart(db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):

    return await cart_service.clear_cart(
        db=db,
        user_id=current_user.id,
    )