from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
        description="Page number, starting from 1.",
        examples=[1],
    )
    size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page (maximum 100).",
        examples=[10],
    )

class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: list[T] = Field(
        description="Items returned for the current page."
    )
    total: int = Field(
        description="Total number of matching items."
    )
    page: int = Field(
        description="Current page number."
    )
    size: int = Field(
        description="Maximum number of items per page."
    )
    pages: int = Field(
        description="Total number of available pages."
    )
