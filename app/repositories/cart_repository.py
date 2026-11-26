from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem


class CartRepository:

    async def create(self, db: AsyncSession, cart: Cart,) -> Cart:

        db.add(cart)
        await db.commit()
        await db.refresh(cart)

        return cart

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID,) -> Cart | None:

        result = await db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_cart_with_items(self, db: AsyncSession, user_id: UUID,) -> Cart | None:
        """
        Retrieve a user's cart with its items and associated products.

        selectinload() efficiently loads collection relationships using
        separate SELECT queries, avoiding duplicated parent rows.

        populate_existing=True refreshes an existing ORM object and its
        eagerly loaded relationships instead of relying on potentially
        stale identity-map state.
        """

        result = await db.execute(
            select(Cart)
            .options(
                selectinload(Cart.cart_items)
                .selectinload(CartItem.product)
            )
            .where(Cart.user_id == user_id)
            .execution_options(populate_existing=True)
        )

        return result.scalar_one_or_none()

    async def get_cart_item(self, db: AsyncSession, cart_id: UUID, product_id: UUID,) -> CartItem | None:

        result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id
            )
        )

        return result.scalar_one_or_none()

    async def create_cart_item(self, db: AsyncSession, cart_item: CartItem,) -> CartItem:

        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)

        return cart_item

    async def get_cart_item_by_id(self, db: AsyncSession, cart_item_id: UUID,) -> CartItem | None:

        result = await db.execute(
            select(CartItem)
            .options(
                selectinload(CartItem.cart),
                selectinload(CartItem.product),
            )
            .where(CartItem.id == cart_item_id)
        )

        return result.scalar_one_or_none()

    async def remove_item(self, db: AsyncSession, cart_item: CartItem,) -> None:

        await db.delete(cart_item)
        await db.commit()

    async def clear_cart(self, db: AsyncSession, cart: Cart,) -> None:

        cart.cart_items.clear() # Because of relationship cascade="all, delete-orphan" between Cart and CartItem, the cart's items are deleted.

    async def save(self, db: AsyncSession,) -> None:

        await db.commit()


cart_repository = CartRepository()
