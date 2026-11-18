from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CartItemResponse(BaseModel):
    id: UUID
    quantity: int
    product: ProductResponse

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "quantity": 2,
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
                }
            ]
        },
    )

class CartResponse(BaseModel):
    id: UUID
    user_id: UUID

    items: list[CartItemResponse]

    total_items: int
    total_price: Decimal

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440004",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440003",
                            "quantity": 2,
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
                        }
                    ],
                    "total_items": 2,
                    "total_price": "1598.00",
                    "created_at": "2026-11-18T10:00:00Z",
                    "updated_at": "2026-11-18T10:05:00Z",
                }
            ]
        },
    )


class AddCartItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "product_id": "550e8400-e29b-41d4-a716-446655440001",
                    "quantity": 2,
                }
            ]
        }
    )

class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(
        ge=0,
        description="New quantity. Use 0 to remove the item.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "quantity": 3,
                }
            ]
        }
    )