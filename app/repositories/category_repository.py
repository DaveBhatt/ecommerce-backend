from uuid import UUID
from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryRepository:

    def create(self, db: Session, category: Category,) -> Category:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def get_by_id(self, db:Session, category_id: UUID,) -> Category | None:
        return (db.query(Category).filter(Category.id == category_id).first())

    def get_by_slug(self, db: Session, slug: str,) -> Category | None:
        return (db.query(Category).filter(Category.slug == slug).first())

    def get_by_name(self, db:Session, name: str, ) -> Category | None:
        return (db.query(Category).filter(Category.name == name).first())
    
    def get_all(self, db: Session,):
        return db.query(Category).all()

    def update(self, db: Session, category: Category,) -> Category:
        db.commit()
        db.refresh(category)
        return category

    def delete(self, db: Session, category: Category,) -> Category:
        category.is_active = False
        db.commit()
        db.refresh(category)
        return category
    
category_repository = CategoryRepository()