from typing import Generic, TypeVar

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
"""ModelType can be any SQLAlchemy model that inherits from Base."""

class BaseRepository(Generic[ModelType]):
    
    def __init__(self, model: type[ModelType]):
        self.model = model

        """
        Now every repository knows which SQLAlchemy model it manages.
        For example:
        ProductRepository(BaseRepository[Product]) will pass:
        Product into the constructor.
        """