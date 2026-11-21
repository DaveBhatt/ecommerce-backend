from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository, category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.slug import generate_slug

class CategoryService:

    def __init__(self, category_repository: CategoryRepository,):
        self.category_repository = category_repository

    async def create_category(self, db: AsyncSession, category_data: CategoryCreate,) -> Category:
        """Responsibilities:

        Check if the name already exists.
        Generate a slug.
        Create the ORM object.
        Save it via the repository.
        Return the created category.

        Notice that slug generation belongs in the service, not in the repository."""

        existing_category = await self.category_repository.get_by_name(
            db,
            category_data.name,
        )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category already exists.",
            )

        category = Category(
            name=category_data.name,
            slug=generate_slug(category_data.name),
            description=category_data.description,
        )

        return await self.category_repository.create(db, category)


    async def get_category(self, db: AsyncSession, category_id: UUID,) -> Category:

        category = await self.category_repository.get_by_id(
            db,
            category_id,
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return category

    async def get_active_category(self, db: AsyncSession, category_id: UUID,) -> Category:

        category = await self.get_category(db, category_id)

        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return category


    async def list_categories(self, db: AsyncSession,) -> list[Category]:

        return await self.category_repository.get_all(db)


    async def update_category(self, db: AsyncSession, category_id: UUID, category_data: CategoryUpdate,) -> Category:

        category = await self.get_category(db, category_id,)
        update_data = category_data.model_dump(exclude_unset=True,)

        if "name" in update_data:
            existing_category = await self.category_repository.get_by_name(
                db,
                update_data["name"],
            )
            if (existing_category and existing_category.id != category.id):

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category already exists.",
                )

            category.slug = generate_slug(update_data["name"],)

        for field, value in update_data.items():
            setattr(category, field, value)

        return await self.category_repository.update(
            db,
            category,
        )


    async def delete_category(self, db: AsyncSession, category_id: UUID,) -> Category:

        category = await self.get_category(
            db,
            category_id,
        )

        return await self.category_repository.delete(db, category,)


category_service = CategoryService(category_repository)