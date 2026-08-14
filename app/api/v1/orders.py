from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.order import CreateOrderRequest, OrderResponse, OrderSummaryResponse
from app.services.order_service import order_service

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)
@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED,)
def create_order(order_data: CreateOrderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),):

    return order_service.create_order(
        db=db,
        user_id=current_user.id,
        order_data=order_data,
    )

@router.get("", response_model=list[OrderSummaryResponse], status_code=status.HTTP_200_OK,)
def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db),):

    return order_service.get_user_orders(
        db=db,
        user_id=current_user.id,
    )

@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK,)
def get_order(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),):

    return order_service.get_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )

@router.post("/{order_id}/cancel", response_model=OrderResponse, status_code=status.HTTP_200_OK,)
def cancel_order(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),):

    return order_service.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
    )