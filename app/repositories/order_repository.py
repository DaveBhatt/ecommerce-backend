from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:

    async def create(self, db: AsyncSession, order: Order,) -> Order:
        db.add(order)
        # db.commit()
        # db.refresh(order)
        await db.flush() # This is the equivalent of commit() but without committing the transaction so we can rollback if needed.

        return order

    async def get_by_id(self, db: AsyncSession, order_id: UUID,) -> Order | None:

        """Finds an order with the given ID."""

        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
            )
            .where(Order.id == order_id)
        )

        return result.scalar_one_or_none()


    async def get_by_id_for_user(self, db: AsyncSession, order_id: UUID, user_id: UUID,) -> Order | None:

        """Finds an order with the given ID for the given user.
        Order ID matches?
               ↓
              YES
               ↓
        User ID matches?
               ↓
              YES
               ↓
        Return order"""

        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
            )
            .where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
        )
        # This query uses selectinload() to eagerly load the order_items and their associated products in a single query.

        return result.scalar_one_or_none()

    async def get_all_by_user_id(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 10,) -> list[Order]:

        """Finds all orders for the given user seperated by pagination."""

        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(
                Order.created_at.desc(),
                Order.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def count_by_user_id(self, db: AsyncSession, user_id: UUID,) -> int:

        result = await db.execute(
            select(func.count(Order.id))
            .where(Order.user_id == user_id)
        )

        return result.scalar_one()


order_repository = OrderRepository()