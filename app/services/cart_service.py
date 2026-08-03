from decimal import Decimal
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from app.models.cart import Cart

from app.repositories.cart_repository import cart_repository

logger = logging.getLogger(__name__)


class CartService:

    def __init__(self):

        """
        Dependency Injection 
        Using __init__ makes it easier to swap implementations
        later and improves testability.
        """
        self.cart_repository = cart_repository

    def get_or_create_cart(self, db: Session, user_id: UUID,) -> Cart:

        cart = self.cart_repository.get_by_user_id(
                db=db,
                user_id=user_id,
        )

        if cart:
            logger.info(
                "Existing cart found for user %s",
                user_id,
            )
            return cart
        
        logger.info(
            "Creating new cart for user %s",
            user_id,
        )

        cart = Cart(user_id=user_id,)

        return self.cart_repository.create(
            db=db,
            cart=cart,
        )
    
    def get_cart(self, db: Session, user_id: UUID,) -> dict:

        logger.info(
            "Fetching cart for user %s",
            user_id,
        )

        cart = self.get_or_create_cart(
            db=db,
            user_id=user_id,
        )

        cart = self.cart_repository.get_cart_with_items(
            db=db,
            user_id=user_id,
        )

        return {
            "id": cart.id,
            "user_id": cart.user_id,
            "items": cart.cart_items,   # Mapping cart_items to items without changing the SQLAlchemy model. The schema will handle the conversion to CartItemResponse.
            "total_items": self.calculate_total_items(cart),
            "total_price": self.calculate_total_price(cart),
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
        }
    
    def calculate_total_items(self, cart: Cart,) -> int:
        
        return sum(
            item.quantity for item in cart.cart_items
        )
    
    def calculate_total_price(self, cart: Cart,) -> Decimal:
        
        return sum(
            (item.quantity * item.product.price for item in cart.cart_items),
            start=Decimal("0.00"),
        )
    
cart_service = CartService()


