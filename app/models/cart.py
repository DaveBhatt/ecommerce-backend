from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    # TYPE_CHECKING avoids circular imports while still giving type hints.
    from app.models.user import User
    from app.models.cart_item import CartItem


class Cart(UUIDMixin, TimestampMixin, Base):

    __tablename__ = "carts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="cart",
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"    # If cart is deleted, we delete the cart items.
    )