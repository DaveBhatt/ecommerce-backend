from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import category_service

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
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


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED,)
async def create_category(category_data: CategoryCreate, db: Session = Depends(get_db),):
    
    return category_service.create_category(
        db=db,
        category_data=category_data,
    ) 

@router.get("", response_model=list[CategoryResponse],)
async def get_categories(db: Session = Depends(get_db),):
    
    return category_service.list_categories(db)

@router.get("/{category_id}", response_model=CategoryResponse,)
async def get_category(category_id: UUID, db: Session = Depends(get_db),):
    
    return category_service.get_category(
        db=db,
        category_id=category_id,
    )

@router.patch("/{category_id}", response_model=CategoryResponse,)

async def update_category(category_id: UUID, category_data: CategoryUpdate, db: Session = Depends(get_db),):
    
    return category_service.update_category(
        db=db,
        category_id=category_id,
        category_data=category_data,
    )

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT,)
async def delete_category(category_id: UUID, db: Session = Depends(get_db),):

    category_service.delete_category(
        db=db,
        category_id=category_id,
    )