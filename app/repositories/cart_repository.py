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

    def save(self, db: Session,) -> None:
        
        db.commit()


cart_repository = CartRepository()
