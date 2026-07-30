from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.product import Product


class CartItem(UUIDMixin, TimestampMixin, Base):

    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "product_id",
            name="uq_cart_product",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_cart_item_quantity_positive",
        ),
    )

    cart_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "carts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    """
        An administrator tries to delete a product.
        We don't want existing carts to suddenly reference a deleted product.
        The database prevents this.
    """

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="cart_items",
    )

    product: Mapped["Product"] = relationship(
        "Product",
    )