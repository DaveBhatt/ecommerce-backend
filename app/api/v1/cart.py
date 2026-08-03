from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.cart import CartResponse
from app.services.cart_service import cart_service


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)

@router.get("", response_model=CartResponse, status_code=status.HTTP_200_OK,)
def get_cart(current_user: User = Depends(get_current_user), db: Session =  Depends(get_db),):

    return cart_service.get_cart(
        db=db,
        user_id=current_user.id,
    )