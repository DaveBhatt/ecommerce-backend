from math import ceil
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.product import Product
from app.repositories.product_repository import product_repository
from app.repositories.category_repository import category_repository
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.slug import generate_slug


class ProductService:

    def __init__(self):
        self.product_repository = product_repository
        self.category_repository = category_repository


    async def create_product(self, db: AsyncSession, product_data: ProductCreate,) -> Product:

        logger.info("Creating product with SKU=%s", product_data.sku)
        """
        API
         │
         ▼
        ProductService.create_product()
         │
         ├── Check category exists
         ├── Check SKU is unique
         ├── Generate slug
         ├── Create Product model
         └── Save using ProductRepository
         │
         ▼
        Repository
         │
         ▼
        Database
        """

        category = await self.category_repository.get_by_id(
            db=db,
            category_id=product_data.category_id,
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )

        existing_product = await self.product_repository.get_by_sku(
            db=db,
            sku=product_data.sku,
        )

        if existing_product:
            logger.warning(
                "Product creation failed. Duplicate SKU=%s",
                product_data.sku,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists.",
            )
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock_quantity=product_data.stock_quantity,
            sku=product_data.sku,
            slug=generate_slug(product_data.name),
            category_id=product_data.category_id,
        )

        logger.info(
            "Product created successfully. ID=%s SKU=%s",
            product.id,
            product.sku,
        )

        return await self.product_repository.create(db=db, product=product,)


    async def get_product_by_id(self, db: AsyncSession, product_id: UUID,) -> Product:

        """Returns 404 if missing"""

        product = await self.product_repository.get_by_id(
            db=db,
            product_id=product_id,
        )

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        return product

    async def get_all_products(
            self,
            db: AsyncSession,
            page: int = 1,
            size: int = 10,
            category_id: UUID | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            search: str | None = None,
            sort: str | None = None,
    ) -> dict:

        """Returns list (possibly empty)"""

        skip = (page - 1) * size

        logger.info(
            "Fetching products page=%s size=%s category=%s min_price=%s max_price=%s search=%s sort=%s",
            page,
            size,
            category_id,
            min_price,
            max_price,
            search,
            sort,
        )

        products =  await self.product_repository.get_all(
            db=db,
            skip=skip,
            limit=size,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
            sort=sort
        )

        total = await self.product_repository.count(
            db=db,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        return {
            "items": products,
            "total": total,
            "page": page,
            "size": size,
            "pages": ceil(total / size) if total else 0,
        }

    async def update_product(self, db: AsyncSession, product_id: UUID, product_data: ProductUpdate,) -> Product:

        """
        update_product()
        │
        ├── Get product
        ├── 404 if missing
        ├── model_dump(exclude_unset=True)
        ├── Validate category (if changed)
        ├── Validate SKU (if changed)
        ├── Regenerate slug (if name changed)
        ├── Apply updates
        └── Repository.update()
        """

        product = await self.get_product_by_id(db=db, product_id=product_id,)

        update_data = product_data.model_dump(exclude_unset=True) # Only the fields actually provided by the client are updated.

        if "category_id" in update_data:
            category = await self.category_repository.get_by_id(
                db=db,
                category_id=update_data["category_id"],
            )

            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found.",
                )

        if "sku" in update_data:    # IQ
            existing_product = await self.product_repository.get_by_sku(
                db=db,
                sku=update_data["sku"],
            )

            if (existing_product and existing_product.id != product.id):

                """The duplicate check should only fail if another product owns the SKU,
                    i.e. another product with same SKU but different product_id exists. """

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists.",
                )

        if "name" in update_data:
            update_data["slug"] = generate_slug(update_data["name"])

        for field, value in update_data.items():
            setattr(product, field, value)

        return await self.product_repository.update(
            db=db,
            product=product,
        )

    async def delete_product(self, db: AsyncSession, product_id: UUID,) -> Product:

        product = await self.get_product_by_id(
            db=db,
            product_id=product_id,
        )
        return await self.product_repository.delete(
            db=db,
            product=product,
        )


product_service = ProductService()
