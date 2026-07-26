from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from pydantic.generics import GenericModel


T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)

class PaginatedResponse(GenericModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
