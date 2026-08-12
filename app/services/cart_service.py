from decimal import Decimal
from uuid import UUID
from app.core.logging import logger

from sqlalchemy.orm import Session
from app.models.cart import Cart
from app.models.cart_item import CartItem

from app.repositories.cart_repository import cart_repository
from app.repositories.product_repository import product_repository

from app.exceptions.product import ProductNotFoundError, ProductInactiveError, InsufficientStockError
from app.exceptions.cart import CartNotFoundError, CartItemNotFoundError

class CartService:

    def __init__(self):

        """
        Dependency Injection 
        Using __init__ makes it easier to swap implementations
        later and improves testability.
        """
        self.cart_repository = cart_repository
        self.product_repository = product_repository

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
            "items": cart.cart_items,   # cart.cart_items becomes items in the response model, which is a list of CartItemResponse objects.
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

    def add_item(self, db: Session, user_id: UUID, product_id: UUID, quantity: int,) -> dict:

        """
        POST /cart/items
                │
                ▼
        Get/Create Cart
                │
                ▼
        Find Product
                │
                ├── Not found → Error
                │
                ▼
        Is Active?
                │
                ├── No → Error
                │
                ▼
        Enough Stock?
                │
                ├── No → Error
                │
                ▼
        Already in Cart?
              ┌─┴─────────────┐
              │               │
             Yes             No
              │               │
        Increase Qty     Create Item
              │               │
              └───────┬───────┘
                      ▼
                   Save Changes
                      ▼
                 Return Cart
        """

        logger.info(
            "Adding product %s (quantity %s) to cart for user %s",
            product_id,
            quantity,
            user_id,
        )

        # Get or create the user's cart
        cart = self.get_or_create_cart(
            db=db,
            user_id=user_id,
        )

        # Fetch the product
        product = self.product_repository.get_by_id(
            db=db,
            product_id=product_id,
        )

        if product is None:
            logger.warning(
                "Product %s not found",
                product_id,
            )
            raise ProductNotFoundError()

        # Product must be active
        if not product.is_active:
            logger.warning(
                "Attempt to add inactive product %s to cart",
                product_id,
            )
            raise ProductInactiveError()

        # Validate requested quantity against stock
        if quantity > product.stock_quantity:
            logger.warning(
                "Requested quantity (%s) exceeds stock (%s) for product %s",
                quantity,
                product.stock_quantity,
                product_id,
            )
            raise InsufficientStockError()

        # Check whether the product is already in the cart
        cart_item = self.cart_repository.get_cart_item(
            db=db,
            cart_id=cart.id,
            product_id=product.id,
        )

        if cart_item:

            new_quantity = cart_item.quantity + quantity if cart_item else quantity

            if new_quantity > product.stock_quantity:
                logger.warning(
                    "Updated quantity (%s) exceeds stock (%s) for product %s",
                    new_quantity,
                    product.stock_quantity,
                    product_id,
                )
                raise InsufficientStockError()

            cart_item.quantity = new_quantity

            self.cart_repository.save(db)

            logger.info(
                "Updated quantity for product %s in cart %s to %s",
                product.id,
                cart.id,
                new_quantity,
            )

        else:

            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
            )

            self.cart_repository.create_cart_item(
                db=db,
                cart_item=cart_item,
            )

            logger.info(
                "Added product %s to cart %s",
                product.id,
                cart.id,
            )

        return self.get_cart(
            db=db,
            user_id=user_id,
        )

    def update_quantity(self, db: Session, user_id: UUID, cart_item_id: UUID, quantity: int,) -> dict:

        """
        PATCH /cart/items/{id}
                    │
                    ▼
        Find CartItem
                    │
              Exists?
              │     │
             No    Yes
              │      │
              ▼      ▼
        404      Owner?
                   │
              No ──┘
              │
              ▼
        404

        Owner
           │
           ▼
        Quantity == 0 ?
             │
         ┌───┴────┐
         │        │
        Yes      No
         │        │
        Delete   Check Stock
         │        │
         └────┬───┘
              ▼
         Save Changes
              ▼
         Return Cart
        
        """

        logger.info(
            "Updating quantity for cart item %s to %s",
            cart_item_id,
            quantity,
        )

        cart_item = self.cart_repository.get_cart_item_by_id(
            db=db,
            cart_item_id=cart_item_id,
        )

        if cart_item is None:
            raise CartItemNotFoundError()

        # Security check
        if cart_item.cart.user_id != user_id:
            raise CartItemNotFoundError()

        # Quantity = 0 means remove the item from the cart
        if quantity == 0:
            self.cart_repository.remove_item(
                db=db,
                cart_item=cart_item,
            )

            logger.info(
                "Removed cart item %s because its quantity became 0",
                cart_item_id,
            )

            return self.get_cart(
                db=db,
                user_id=user_id,
            )

        # Check stock
        if quantity > cart_item.product.stock_quantity:
            raise InsufficientStockError()

        cart_item.quantity = quantity

        self.cart_repository.save(db)

        logger.info(
            "Updated quantity for cart item %s to %s",
            cart_item_id,
            quantity,
        )

        return self.get_cart(
            db=db,
            user_id=user_id,
        )


    def remove_item(self, db: Session, user_id: UUID, cart_item_id: UUID,) -> dict:

        logger.info(
            "Removing cart item %s",
            cart_item_id,
        )

        cart_item = self.cart_repository.get_cart_item_by_id(
            db=db,
            cart_item_id=cart_item_id,
        )

        if cart_item is None:
            raise CartItemNotFoundError()

        # Ownership check
        if cart_item.cart.user_id != user_id:
            raise CartItemNotFoundError()

        self.cart_repository.remove_item(
            db=db,
            cart_item=cart_item,
        )

        logger.info(
            "Removed cart item %s",
            cart_item_id,
        )

        return self.get_cart(
            db=db,
            user_id=user_id,
        )


    def clear_cart(self, db: Session, user_id: UUID,) -> dict:

        logger.info(
            "Clearing cart for user %s",
            user_id,
        )

        cart = self.get_or_create_cart(
            db=db,
            user_id=user_id,
        )   
        # This is a performance optimization. We don't need to fetch the cart from the database if it doesn't exist.

        self.cart_repository.clear_cart(
            db=db,
            cart=cart,
        )

        logger.info(
            "Cart cleared for user %s",
            user_id,
        )

        return self.get_cart(
            db=db,
            user_id=user_id,
        )
        
cart_service = CartService()


