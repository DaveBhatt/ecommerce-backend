from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repository import product_repository
from app.repositories.category_repository import category_repository
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.slug import generate_slug


class ProductService:

    def __init__(self):
        self.product_repository = product_repository
        self.category_repository = category_repository


    def create_product(self, db: Session, product_data: ProductCreate,) -> Product:
        
        product = Product(
            **product_data.model_dump(exclude={"slug"}),
            slug=generate_slug(product_data.name),
        )

        return self.product_repository.create(db=db, product=product,)
    
    
    def get_product_by_id()



product_service = ProductService()