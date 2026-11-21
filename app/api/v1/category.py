from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import category_service
from app.api.responses import COMMON_ERROR_RESPONSES, problem_response

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={
        **COMMON_ERROR_RESPONSES,
        404: problem_response("Category not found."),
    },
)


"""
Architecture:

HTTP Request
      │
      ▼
Router Function
      │
      ▼
CategoryService
      │
      ▼
CategoryRepository
      │
      ▼
Database


Responibilities:
receiving the HTTP request
validating it with Pydantic
injecting dependencies (db, authenticated user, etc.)
calling the appropriate service method
returning the response

"""


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    description=(
        "Create a new product category using the supplied category details. "
        "Returns the newly created category with its assigned identifier."
    ),
)
async def create_category(category_data: CategoryCreate, db: AsyncSession = Depends(get_async_db),):
    
    return await category_service.create_category(
        db=db,
        category_data=category_data,
    ) 

@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List categories",
    description=(
        "Retrieve a list of available product categories. "
        "Returns category information for each category."
    ),
)
async def get_categories(db: AsyncSession = Depends(get_async_db),):
    
    return await category_service.list_categories(db)

@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
    description=(
        "Retrieve a specific product category using its UUID. "
        "Returns the category details if it exists."
    ),
)
async def get_category(category_id: UUID, db: AsyncSession = Depends(get_async_db),):
    
    return await category_service.get_active_category(
        db=db,
        category_id=category_id,
    )

@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
    description=(
        "Partially update an existing product category using its UUID. "
        "Provide the fields that need to be changed. "
        "Returns the updated category."
    ),
)
async def update_category(category_id: UUID, category_data: CategoryUpdate, db: AsyncSession = Depends(get_async_db),):
    
    return await category_service.update_category(
        db=db,
        category_id=category_id,
        category_data=category_data,
    )

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description=(
        "Delete an existing product category using its UUID. "
        "Returns HTTP 204 No Content when the deletion succeeds."
    ),
)
async def delete_category(category_id: UUID, db: AsyncSession = Depends(get_async_db),):

    await category_service.delete_category(
        db=db,
        category_id=category_id,
    )