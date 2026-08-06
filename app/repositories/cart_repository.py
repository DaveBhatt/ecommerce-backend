from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem


class CartRepository:

    def create(self, db: Session, cart: Cart,) -> Cart:
        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart
    
    def get_by_user_id(self, db: Session, user_id: UUID,) -> Cart | None:
        
        return (
            db.query(Cart)
            .filter(Cart.user_id == user_id)
            .first()
        )
    
    def get_cart_with_items(self, db: Session, user_id: UUID,) -> Cart | None:

        return (
            db.query(Cart)
            .options(
                selectinload(Cart.cart_items).selectinload(CartItem.product)
            )
            .filter(Cart.user_id == user_id)
            .first()
        )
        # This query uses selectinload() to eagerly load the cart_items and their associated products in a single query.
        # The .filter(Cart.user_id == user_id) ensures that we only fetch the cart for the specified user.
        """
        selectinload produces separate SQL queries using WHERE IN (...).

        Good when:

        one-to-many
        collections
        avoids duplicated rows

        For shopping carts, selectinload() is generally the better choice.
        
        
        Alternatively joinedload produces one large SQL JOIN.

        Good when:

        few rows
        one-to-one relationships
        
        """

    def get_cart_item(self, db: Session, cart_id: UUID, product_id: UUID,) -> CartItem | None:

        return (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id, 
                    CartItem.product_id == product_id)
                    .first()
                )

    def create_cart_item(self, db: Session, cart_item: CartItem,) -> CartItem:

        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item

    def get_cart_item_by_id(self, db: Session, cart_item_id: UUID,) -> CartItem | None:

        return (
            db.query(CartItem)
            .filter(CartItem.id == cart_item_id)
            .first()
        )

    def remove_item(self, db: Session, cart_item: CartItem,) -> None:
        
        db.delete(cart_item)
        db.commit()

    def clear_cart(self, db: Session, cart: Cart,) -> None:

        cart.cart_items.clear() # Because of relationship cascade="all, delete-orphan" between Cart and CartItem, the cart's items are deleted.
        db.commit()

    def save(self, db: Session,) -> None:
        
        db.commit()

    
    


cart_repository = CartRepository()
