from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=255, description="Product name",)
    description: str | None = Field(default=None, max_length=1000, description="Product description",)
    price: Decimal = Field(ge=0, decimal_places=2, max_digits=10, description="Product price",)
    stock_quantity: int = Field(default=0, ge=0, description="Available stock",)
    category_id: UUID

class ProductCreate(ProductBase):
    sku: str = Field(min_length=3, max_length=100, description="Stock Keeping Unit",)

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255,)
    description: str | None = None
    sku: str | None = Field(default=None, min_length=3, max_length=100,)
    price: Decimal | None = Field(default=None, ge=0,)
    stock_quantity: int | None = Field(default=None, ge=0,)
    category_id: UUID | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    slug: str
    sku: str
    is_active: bool
    created_at: datetime
    updated_at: datetime