from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.database.session import get_async_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.product_service import product_service
from app.api.responses import COMMON_ERROR_RESPONSES, problem_response


router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={
        **COMMON_ERROR_RESPONSES,
        404: problem_response("Product not found."),
        400: problem_response("The product request could not be processed."),
    },
)
@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
    description=(
        "Create a new product using the supplied product details. "
        "Requires an authenticated user. Returns the newly created "
        "product with its assigned identifier and other product information."
    ),
)
async def create_product(product_data: ProductCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):
    
    return await product_service.create_product(
        db=db,
        product_data=product_data,
    )

@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List products",
    description=(
        "Retrieve a paginated list of products. Supports filtering by category "
        "and price range, searching products, and sorting results. "
        "Pagination and filter options can be supplied as query parameters."
    ),
)
async def get_all_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: UUID | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, min_length=1),
    sort: str | None = Query(
        default=None,
        description="Allowed: name, -name, price, -price, created_at, -created_at,"
    ),
    db: AsyncSession = Depends(get_async_db),
):

    return await product_service.get_all_products(
        db=db,
        page=page,
        size=size,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort=sort,
    )

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a product by ID",
    description=(
        "Retrieve the details of a specific product using its UUID. "
        "Returns the product information if it exists."
    ),
)
async def get_product_by_id(product_id: UUID, db: AsyncSession = Depends(get_async_db),):

    return await product_service.get_active_product_by_id(
        db=db,
        product_id=product_id,
    )

@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product",
    description=(
        "Partially update an existing product using its UUID. "
        "Provide the fields that need to be changed. "
        "Requires an authenticated user and returns the updated product."
    ),
)
async def update_product(product_id: UUID, product_data: ProductUpdate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):

    return await product_service.update_product(
        db=db,
        product_id=product_id,
        product_data=product_data,
    )

@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a product",
    description=(
        "Remove a product from the active product catalog using its UUID. "
        "Requires an authenticated user and returns the product information."
    ),
)
async def delete_product(product_id: UUID, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user),):

    return await product_service.delete_product(
        db=db,
        product_id=product_id,
    )