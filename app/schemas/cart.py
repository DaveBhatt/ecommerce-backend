from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quantity: int
    product: ProductResponse

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    items: list[CartItemResponse]

    total_items: int
    total_price: Decimal

    created_at: datetime
    updated_at: datetime

class AddCartItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1)

class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(
        ge=0,
        description="New quantity. Use 0 to remove the item.",
    )