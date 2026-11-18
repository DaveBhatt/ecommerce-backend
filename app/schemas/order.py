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
    id: UUID
    product: ProductResponse # This is the product that was ordered.
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440006",
                    "product": {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Wireless Mouse",
                        "description": "Ergonomic wireless mouse with adjustable DPI.",
                        "price": "799.00",
                        "stock_quantity": 50,
                        "category_id": "550e8400-e29b-41d4-a716-446655440000",
                        "slug": "wireless-mouse",
                        "sku": "ELEC-MOUSE-001",
                        "is_active": True,
                        "created_at": "2026-11-18T10:00:00Z",
                        "updated_at": "2026-11-18T10:00:00Z",
                    },
                    "quantity": 2,
                    "unit_price": "799.00",
                    "subtotal": "1598.00",
                }
            ]
        },
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "shipping_address": "432 Main Street, Parkson Boulevard, New Delhi, India"
                }
            ]
        }
    )

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    items: list[OrderItemResponse]  # This is the list of items in the order. We'll map order.order_items to items in service layer.
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440007",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "status": "PENDING",
                    "total_amount": "1598.00",
                    "shipping_address": "432 Main Street, Parkson Boulevard, New Delhi, India",
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440006",
                            "product": {
                                "id": "550e8400-e29b-41d4-a716-446655440001",
                                "name": "Wireless Mouse",
                                "description": "Ergonomic wireless mouse with adjustable DPI.",
                                "price": "799.00",
                                "stock_quantity": 50,
                                "category_id": "550e8400-e29b-41d4-a716-446655440000",
                                "slug": "wireless-mouse",
                                "sku": "ELEC-MOUSE-001",
                                "is_active": True,
                                "created_at": "2026-11-18T10:00:00Z",
                                "updated_at": "2026-11-18T10:00:00Z",
                            },
                            "quantity": 2,
                            "unit_price": "799.00",
                            "subtotal": "1598.00",
                        }
                    ],
                    "created_at": "2026-11-18T10:10:00Z",
                    "updated_at": "2026-11-18T10:10:00Z",
                }
            ]
        },
    )

class OrderSummaryResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440007",
                    "status": "PENDING",
                    "total_amount": "1598.00",
                    "created_at": "2026-11-18T10:10:00Z",
                }
            ]
        },
    )
