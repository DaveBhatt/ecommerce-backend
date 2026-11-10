from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.models.product import Product

class ProductRepository:

    async def create(self, db: AsyncSession, product: Product,) -> Product:

        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    async def get_by_id(self, db: AsyncSession, product_id: UUID,) -> Product | None:

        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )

        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str,)  -> Product | None:

        result = await db.execute(
            select(Product).where(Product.slug == slug)
        )

        return result.scalar_one_or_none()

    async def get_by_sku(self, db: AsyncSession, sku: str,) -> Product | None:

        result = await db.execute(
            select(Product).where(Product.sku == sku)
        )

        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str,) -> Product | None:

        result = await db.execute(
            select(Product).where(Product.name == name)
        )

        return result.scalar_one_or_none()

    async def get_all(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 10,
            category_id: UUID | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            search: str | None = None,
            sort: str | None = None,
    ) -> list[Product]:

        query = self._build_query(
            db=db,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        sort_columns = {
            "name": Product.name,
            "price": Product.price,
            "created_at": Product.created_at,
        }

        if sort:
            descending = sort.startswith("-")
            field = sort[1:] if descending else sort

            if field in sort_columns:
                column = sort_columns[field]

                query = query.order_by(
                    column.desc() if descending else column.asc()
                )
        else:
            query = query.order_by(Product.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)

        return list(result.scalars().all())

    async def update(self, db: AsyncSession, product: Product,) -> Product:

        await db.commit()
        await db.refresh(product)

        return product

    async def delete(self, db: AsyncSession, product: Product,) -> Product:

        product.is_active = False
        await db.commit()
        await db.refresh(product)

        return product

    async def count(
            self,
            db: AsyncSession,
            category_id: UUID | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            search: str | None = None,
    ) -> int:

        query  = self._build_query(
            db=db,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)

        return result.scalar_one()

    def _build_query(
            self,
            db: AsyncSession,
            category_id: UUID | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            search: str | None = None,
    ):

        """
            _build_query()
                │
                ▼
        returns filtered query
                │
           ┌────┴────┐
           ▼         ▼
        get_all()   count()

        """

        query = select(Product).where(Product.is_active.is_(True))

        if category_id is not None:
            query = query.where(Product.category_id == category_id)

        if min_price is not None:
            query = query.where(Product.price >= min_price)

        if max_price is not None:
            query = query.where(Product.price <= max_price)

        if search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                )
            )

        return query


product_repository = ProductRepository()
