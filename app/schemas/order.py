from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.product import ProductResponse

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product: ProductResponse # This is the product that was ordered.
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

class CreateOrderRequest(BaseModel):

    """The cart already contains the products and quantities, so we don't need to pass those."""

    shipping_address: str = Field(
        min_length=10,
        max_length=500,
        description="Customer's complete shipping address",
        examples=["432 Main Street, Parkson Boulevard, New Delhi, India"],
    )

    @field_validator("shipping_address", mode="before")
    @classmethod
    def validate_shipping_address(cls, value):

        if isinstance(value, str):
            value = value.strip()

        return value

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    items: list[OrderItemResponse]  # This is the list of items in the order. We'll map order.order_items to items in service layer.
    created_at: datetime
    updated_at: datetime

class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
