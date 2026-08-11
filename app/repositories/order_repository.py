from uuid import UUID

from sqlalchemy.orm import Session, selectinload
from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:

    def create(self, db: Session, order: Order,) -> Order:
        db.add(order)
        # db.commit()
        # db.refresh(order)
        db.flush() # This is the equivalent of commit() but without committing the transaction so we can rollback if needed.

        return order

    def get_by_id(self, db: Session, order_id: UUID,) -> Order | None:

        """Finds an order with the given ID."""

        return (
            db.query(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
            )
            .filter(Order.id == order_id)
            .first()
        )
        # This query uses selectinload() to eagerly load the order_items and their associated products in a single query.
        

    def get_by_id_for_user(self, db: Session, order_id: UUID, user_id: UUID,) -> Order | None:

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

        return (
            db.query(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
            )
            .filter(Order.id == order_id,
                    Order.user_id == user_id,
            )
            .first()
        )

    def get_all_by_user_id(self, db: Session, user_id: UUID,) -> list[Order]:

        """Finds all orders for the given user."""

        return (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .all()
        )


order_repository = OrderRepository()