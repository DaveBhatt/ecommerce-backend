from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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

    shipping_address: str

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

