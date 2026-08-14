""" Workflow for creating an order
POST /orders
     │
     ▼
OrderService.create_order()
     │
     ├── Get user's cart
     │
     ├── Check cart
     │
     ├── Validate products
     │
     ├── Validate stock
     │
     ├── Calculate total
     │
     ├── Create Order
     │
     ├── Create OrderItems
     │
     ├── Decrease stock
     │
     ├── Clear cart
     │
     └── Commit transaction
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

from app.repositories.cart_repository import cart_repository
from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository

from app.schemas.order import CreateOrderRequest

from app.exceptions.order import OrderNotFoundError, EmptyCartError, InvalidOrderStatusTransitionError
from app.exceptions.cart import CartNotFoundError
from app.exceptions.product import ProductNotFoundError, ProductInactiveError, InsufficientStockError

ALLOWED_ORDER_TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.PAID,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAID: {
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.DELIVERED,
    },
    OrderStatus.DELIVERED: set(), # Delivery is final (Terminal State)
    OrderStatus.CANCELLED: set(), # Cancellation is final (Terminal State)
}

class OrderService:

    def __init__(self):
        """
        Dependency Injection 
        Using __init__ makes it easier to swap implementations
        later and improves testability.
        """
        self.cart_repository = cart_repository
        self.order_repository = order_repository
        self.product_repository = product_repository

    def create_order(self, db: Session, user_id: UUID, order_data: CreateOrderRequest,) -> dict:

        logger.info(
            "Creating order for user %s",
            user_id,
        )

        try:

            # Get user's cart with items and products.
            cart = self.cart_repository.get_cart_with_items(
                db=db,
                user_id=user_id,
            )

            # Validate cart
            if cart is None:
                logger.warning(
                    "Order creation failed. Cart not found for user %s",
                    user_id,
                )
                raise CartNotFoundError()

            # Check for empty cart
            if not cart.cart_items:
                logger.warning(
                    "Order creation failed. Cart is empty for user %s",
                    user_id,
                )
                raise EmptyCartError()

            total_amount = Decimal("0.00")

            # Validate cart items
            for cart_item in cart.cart_items:
                product = cart_item.product

                if product is None:
                    logger.warning(
                        "Product %s not found during checkout",
                        cart_item.product_id,
                    )
                    raise ProductNotFoundError()

                # Check product status
                if not product.is_active:
                    logger.warning(
                        "Checkout failed. Product %s is inactive",
                        product.id,
                    )
                    raise ProductInactiveError()

                # check stock
                if cart_item.quantity > product.stock_quantity:
                    logger.warning(
                        "Checkout failed. Requested quantity (%s) exceeds stock (%s) for product %s",
                        cart_item.quantity,
                        product.stock_quantity,
                        product.id,
                    )
                    raise InsufficientStockError()

                total_amount += (
                    product.price * cart_item.quantity
                )    

            order = Order(
                user_id=user_id,
                status=OrderStatus.PENDING,
                total_amount=total_amount,
                shipping_address=order_data.shipping_address,
            )

            self.order_repository.create(
                db=db,
                order=order,
            )

            # create OrderItems
            for cart_item in cart.cart_items:

                product = cart_item.product

                subtotal = (
                    product.price * cart_item.quantity
                )

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    subtotal=subtotal,
                )

                db.add(order_item) # This is the equivalent of commit() but without committing the transaction so we can rollback if needed.

                product.stock_quantity -= cart_item.quantity

            cart.cart_items.clear() # Because of relationship cascade="all, delete-orphan" between Cart and CartItem, the cart's items are deleted.

            db.commit()
            db.refresh(order)

            logger.info(
                "Order created successfully. Order ID: %s User ID: %s Total Amount: %s",
                order.id,
                user_id,
                total_amount,
            )

            return self._to_order_response(order)

        except Exception:
            db.rollback()

            logger.exception(
                "Order creation failed for user %s",
                user_id,
            )

            raise

    def get_user_orders(self, db: Session, user_id: UUID,) -> list[Order]:

        logger.info(
            "Fetching orders for user %s",
            user_id,
        )

        return self.order_repository.get_all_by_user_id(
            db=db,
            user_id=user_id,
        )

    def get_order(self, db: Session, order_id: UUID, user_id: UUID,) -> dict:

        logger.info(
            "Fetching order %s for user %s",
            order_id,
            user_id,
        )

        order = self.order_repository.get_by_id_for_user(
            db=db,
            order_id=order_id,
            user_id=user_id,
        )

        if order is None:
            logger.warning(
                "Order %s not found for user %s",
                order_id,
                user_id,
            )
            raise OrderNotFoundError()

        return self._to_order_response(order)

    def _to_order_response(self, order: Order,) -> dict:

        return {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "items": order.order_items,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }
    

    def update_status(self, db: Session, order_id: UUID, new_status: OrderStatus,) -> dict:

        logger.info(
            "Updating order %s to status %s",
            order_id,
            new_status,
        )

        order = self.order_repository.get_by_id(
            db=db,
            order_id=order_id,
        )

        if order is None:
            logger.warning(
                "Order %s not found",
                order_id,
            )
            raise OrderNotFoundError()

        old_status = order.status

        allowed_statuses = ALLOWED_ORDER_TRANSITIONS.get(
            old_status,
            set(),
        ) # The set() is a placeholder for the allowed statuses. It will be replaced with the actual allowed statuses.

        if new_status not in allowed_statuses:
            logger.warning(
                "Invalid order status transition. %s -> %s",
                old_status,
                new_status,
            )
            raise InvalidOrderStatusTransitionError()

        order.status = new_status

        db.commit()
        db.refresh(order)

        logger.info(
            "Order %s status updated from %s to %s",
            order_id,
            old_status,
            new_status,
        )

        return self._to_order_response(order)


    def cancel_order(self, db: Session, order_id: UUID, user_id: UUID,) -> dict:

        """
        JWT
         ↓
        current_user.id
         ↓
        get_by_id_for_user()
         ↓
        only user's order
         ↓
        check transition
         ↓
        cancel"""

        logger.info(
            "Cancelling order %s for user %s",
            order_id,
            user_id,
        )

        order = self.order_repository.get_by_id_for_user(
            db=db,
            order_id=order_id,
            user_id=user_id,
        )

        if order is None:    
            logger.warning(
                "Order %s not found for user %s",
                order_id,
                user_id,
            )
            raise OrderNotFoundError()

        old_status = order.status

        allowed_statuses = ALLOWED_ORDER_TRANSITIONS.get(
            old_status,
            set(),
        )

        if OrderStatus.CANCELLED not in allowed_statuses:
            logger.warning(
                "Order %s cannot be cancelled from status %s",
                order_id,
                old_status,
            )
            raise InvalidOrderStatusTransitionError()

        order.status = OrderStatus.CANCELLED

        db.commit()
        db.refresh(order)

        logger.info(
            "Order %s cancelled successfully",
            order_id,
        )

        return self._to_order_response(order)
    

order_service = OrderService()

