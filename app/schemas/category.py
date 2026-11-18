from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, description="Category name",)
    description: str | None = Field(default=None, max_length=500, description="Category description",)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Electronics",
                    "description": "Electronic devices and accessories.",
                }
            ]
        }
    )

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Consumer Electronics",
                    "description": "Electronic devices, gadgets, and accessories.",
                }
            ]
        }
    )

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "name": "Electronics",
                    "slug": "electronics",
                    "description": "Electronic devices and accessories.",
                    "is_active": True,
                }
            ]
        },
    )