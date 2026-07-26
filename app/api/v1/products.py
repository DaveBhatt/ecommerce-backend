from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.product_service import product_service


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED,)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    
    return product_service.create_product(
        db=db,
        product_data=product_data,
    )

@router.get("", response_model=PaginatedResponse[ProductResponse], status_code=status.HTTP_200_OK,)
def get_all_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):

    return product_service.get_all_products(
        db=db,
        page=page,
        size=size,
    )

@router.get("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK,)
def get_product_by_id(product_id: UUID, db: Session = Depends(get_db),):

    return product_service.get_product_by_id(
        db=db,
        product_id=product_id,
    )

@router.patch("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK,)
def update_product(product_id: UUID, product_data: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):

    return product_service.update_product(
        db=db,
        product_id=product_id,
        product_data=product_data,
    )

@router.delete("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK,)
def delete_product(product_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):

    return product_service.delete_product(
        db=db,
        product_id=product_id,
    )