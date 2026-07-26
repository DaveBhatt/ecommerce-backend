from uuid import UUID
from sqlalchemy.orm import Session
from app.models.product import Product

class ProductRepository:

    def create(self, db: Session, product: Product,) -> Product:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    def get_by_id(self, db: Session, product_id: UUID,) -> Product | None:
        return(db.query(Product).filter(Product.id == product_id).first())
    
    def get_by_slug(self, db: Session, slug: str,)  -> Product | None:
        return(db.query(Product).filter(Product.slug == slug).first())
    
    def get_by_sku(self, db: Session, sku: str,) -> Product | None:
        return(db.query(Product).filter(Product.sku == sku).first())
    
    def get_by_name(self, db: Session, name: str,) -> Product | None:
        return(db.query(Product).filter(Product.name == name).first())
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 10,) -> list[Product]:
        return(db.query(Product)
               .filter(Product.is_active.is_(True))
               .offset(skip)
               .limit(limit)
               .all()
            )
    
    def update(self, db: Session, product: Product,) -> Product:
        db.commit()
        db.refresh(product)
        return product
    
    def delete(self, db: Session, product: Product,) -> Product:
        product.is_active = False
        db.commit()
        db.refresh(product)
        return product
    
    def count(self, db: Session) -> int:
        return(
            db.query(Product)
            .filter(Product.is_active.is_(True))
            .count()
        )
    

product_repository = ProductRepository()
