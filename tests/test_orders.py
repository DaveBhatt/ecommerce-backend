from decimal import Decimal
from uuid import UUID
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

import pytest
from httpx import AsyncClient

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.services.order_service import order_service

from app.exceptions.product import ProductNotFoundError, ProductInactiveError
from app.exceptions.order import InvalidOrderStatusTransitionError, OrderNotFoundError
from app.schemas.order import CreateOrderRequest


@pytest.mark.anyio
async def test_create_order_success(
    authenticated_client: AsyncClient,
    test_product: dict,
    db: AsyncSession,
):
    # Arrange: add two products to users cart.
    cart_response = await authenticated_client.post(
        "api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert cart_response.status_code == 200

    # Act: create an order
    order_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "457 Jane Street, Dehradun, Uttarakhand",
        },
    )

    # Assert: order creation
    assert order_response.status_code == 201

    order = order_response.json()

    assert order["status"] == "PENDING"
    assert order["shipping_address"] == ("457 Jane Street, Dehradun, Uttarakhand")
    assert float(order["total_amount"]) == 1598.00

    # Assert: order contains the expected item
    assert len(order["items"]) == 1

    order_item = order["items"][0]

    assert order_item["product"]["id"] == test_product["id"]
    assert order_item["quantity"] == 2
    assert float(order_item["unit_price"]) == 799.00
    assert float(order_item["subtotal"]) == 1598.00

    # Assert: checkout deducted the purchased quantity from inventory
    product = await db.get(
        Product,
        UUID(test_product["id"]),
    )

    assert product is not None
    assert product.stock_quantity == 48

    # Assert: checkout cleared the cart
    cart_post_checkout = await authenticated_client.get(
        "api/v1/cart"
    )

    assert cart_post_checkout.status_code == 200
    assert cart_post_checkout.json()["items"] == []

@pytest.mark.anyio
async def test_create_order_with_insufficient_stock(
    authenticated_client: AsyncClient,
    test_product: dict,
    db: AsyncSession,
):
    # Arrange: add 5 units to the cart
    cart_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 5,
        },
    )

    assert cart_response.status_code == 200

    # Reduce available stock to 3 through product API
    stock_update_response = await authenticated_client.patch(
        f"/api/v1/products/{test_product['id']}",
        json={
            "stock_quantity": 3,
        },
    )

    assert stock_update_response.status_code == 200

    # Act: attempt checkout
    order_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "457 Jane Street, Dehradun, Uttarakhand",
        },
    )

    # Assert: checkout is rejected
    assert order_response.status_code == 400

    assert order_response.headers["content-type"].startswith(
        "application/problem+json"
    )

    assert order_response.json()["code"] == "INSUFFICIENT_STOCK"
    assert order_response.json()["detail"] == "Insufficient stock available."

    # Assert: cart remains unchanged
    cart_post_failure = await authenticated_client.get(
        "/api/v1/cart"
    )

    assert cart_post_failure.status_code == 200
    assert len(cart_post_failure.json()["items"]) == 1
    assert cart_post_failure.json()["items"][0]["quantity"] == 5

    # Assert: failed checkout did not create an order.
    result = await db.execute(
        select(func.count()).select_from(Order)
    )

    assert result.scalar_one() == 0

    # Assert: failed checkout does not modify product inventory.
    product = await db.get(Product, UUID(test_product["id"]))

    assert product is not None
    assert product.stock_quantity == 3

@pytest.mark.anyio
async def test_create_order_rolls_back_on_failure(
    authenticated_client: AsyncClient,
    test_product: dict,
    db: AsyncSession,
    monkeypatch,
):
    # Arrange: add two products to the cart
    cart_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert cart_response.status_code == 200

    # Preserve the original respository method
    original_clear_cart = order_service.cart_repository.clear_cart

    # Stimulate a failure after cart clearing but before commit
    async def failing_clear_cart(*, db, cart):
        await original_clear_cart(
            db=db,
            cart=cart,
        )

        raise RuntimeError("Simulated checkout failure.")

    monkeypatch.setattr(
        order_service.cart_repository,
        "clear_cart",
        failing_clear_cart,
    )

    # Act: checkout should raise the simulated exception
    with pytest.raises(
        RuntimeError,
        match="Simulated checkout failure.",
    ):
        await authenticated_client.post(
            "/api/v1/orders",
            json={
                "shipping_address": "457 Jane Street, Dehradun, Uttarakhand",
            },
        )

    # Assert: no order was persisted
    order_count = await db.scalar(
        select(func.count()).select_from(Order)
    )

    assert order_count == 0

    # Assert: no order items were persisted
    order_item_count = await db.scalar(
        select(func.count()).select_from(OrderItem)
    )

    assert order_item_count == 0

    # Assert: product inventory was restored by rollback
    product = await db.get(
        Product,
        test_product["id"],
    )

    assert product is not None
    assert product.stock_quantity == 50

    # Assert: cart contents were preserved
    cart_post_failure = await authenticated_client.get(
        "/api/v1/cart"
    )

    assert cart_post_failure.status_code == 200
    assert len(cart_post_failure.json()["items"]) == 1
    assert cart_post_failure.json()["items"][0]["quantity"] == 2

@pytest.mark.anyio
async def test_get_order_by_id_success(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Arrange: add a product to the cart.
    cart_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert cart_response.status_code == 200

    # Create order
    create_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "457 Jane Street, Dehradun, Uttarakhand",
        },
    )

    created_order = create_response.json()
    order_id = created_order["id"]

    # Act: retrieve the order using its ID
    response = await authenticated_client.get(
        f"/api/v1/orders/{order_id}"
    )

    # Assert: successful retreival
    assert response.status_code == 200

    retrieved_order = response.json()

    assert retrieved_order["id"] == order_id
    assert retrieved_order["status"] == "PENDING"
    assert retrieved_order["shipping_address"] == ("457 Jane Street, Dehradun, Uttarakhand")

    # Verify order items
    assert len(retrieved_order["items"]) == 1

    item = retrieved_order["items"][0]

    assert item["product"]["id"] == test_product["id"]
    assert item["quantity"] == 2
    assert float(item["unit_price"]) == 799.00
    assert float(item["subtotal"]) == 1598.00

@pytest.mark.anyio
async def test_get_order_by_id_forbidden_for_another_user(
    authenticated_client: AsyncClient,
    client: AsyncClient,
    test_product: dict,
):
    # Arrange: create an order as the first user.
    await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    create_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "457 Jane Street, Dehradun, Uttarakhand",
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    # Register a different user.
    second_user = {
        "email": "seconduser@example.com",
        "username": "seconduser",
        "password": "StrongPassword@123",
        "full_name": "Second User",
    }

    register_response = await client.post(
        "/api/v1/auth/register",
        json=second_user,
    )

    assert register_response.status_code == 201

    # Authenticate the second user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": second_user["email"],
            "password": second_user["password"],
        },
    )

    assert login_response.status_code == 200

    second_user_headers = {
        "Authorization": (
            f"Bearer {login_response.json()["access_token"]}"
        ),
    }

    # Act: attempt to retrieve the first user's order.
    response = await authenticated_client.get(
        f"/api/v1/orders/{order_id}",
        headers=second_user_headers,
    )

    # Assert: access is denied.
    assert response.status_code == 404

@pytest.mark.anyio
async def test_get_order_by_id_not_found(
    authenticated_client: AsyncClient,
):
    # Generate an order ID that does not exist.
    order_id = uuid4()

    response = await authenticated_client.get(
        f"/api/v1/orders/{order_id}"
    )

    assert response.status_code == 404

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 404
    assert data["title"] == "Not Found"

@pytest.mark.anyio
async def test_get_orders_pagination(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Create three orders for the authenticated user.
    for _ in range(3):
        cart_response = await authenticated_client.post(
            "/api/v1/cart/items",
            json={
                "product_id": test_product["id"],
                "quantity": 1,
            },
        )
        assert cart_response.status_code == 200

        order_response = await authenticated_client.post(
            "/api/v1/orders",
            json={
                "shipping_address": "123 Main Street, New Delhi, India",
            },
        )
        assert order_response.status_code == 201

    # Request the first page with two orders per page.
    response = await authenticated_client.get(
        "/api/v1/orders",
        params={
            "page": 1,
            "size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] == 2

@pytest.mark.anyio
async def test_cancel_order_restores_inventory(
    authenticated_client: AsyncClient,
    test_product: dict
):
    # Add two units of test_product to cart.
    cart_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )
    assert cart_response.status_code == 200

    # Create an order.
    order_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "123 Test Street, Dehradun, Uttarakhand",
        },
    )
    assert order_response.status_code == 201

    order = order_response.json()

    # Verify inventory was deducted.
    product_response = await authenticated_client.get(
        f"/api/v1/products/{test_product['id']}"
    )
    assert product_response.json()["stock_quantity"] == test_product["stock_quantity"] - 2

    # Cancel the order.
    cancellation_response = await authenticated_client.post(
        f"/api/v1/orders/{order['id']}/cancel"
    )

    assert cancellation_response.status_code == 200

    cancelled_order = cancellation_response.json()
    assert cancelled_order["status"] == "CANCELLED"
    assert cancelled_order["items"][0]["quantity"] == 2

    # Verify inventory was restored.
    product_response = await authenticated_client.get(
        f"/api/v1/products/{test_product['id']}"
    )
    assert product_response.json()["stock_quantity"] == test_product["stock_quantity"]

@pytest.mark.anyio
async def test_cancel_order_twice_does_not_restore_inventory_twice(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Add two units to cart.
    await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    # Create an order.
    order_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "123 Test Street, Dehradun, Uttarakhand",
        },
    )
    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    # Cancel the order for the first time.
    first_response = await authenticated_client.post(
        f"/api/v1/orders/{order_id}/cancel"
    )
    assert first_response.status_code == 200

    # Verify inventory was restored.
    product_response = await authenticated_client.get(
        f"/api/v1/products/{test_product['id']}"
    )
    restored_stock = product_response.json()["stock_quantity"]

    assert restored_stock == test_product["stock_quantity"]

    # Attempt cancellation again.
    second_response = await authenticated_client.post(
        f"/api/v1/orders/{order_id}/cancel"
    )

    assert second_response.status_code == 400

    # Verify inventory was not restored a second time.
    product_response = await authenticated_client.get(
        f"/api/v1/products/{test_product['id']}"
    )

    assert product_response.json()["stock_quantity"] == restored_stock

@pytest.mark.anyio
async def test_cancel_order_forbidden_for_another_user(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # User A adds two units to cart.
    await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    # User A creates an order.
    order_response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "123 Test Street, Dehradun, Uttarakhand",
        },
    )
    assert order_response.status_code == 201

    order = order_response.json()

    # Create unique credentials for User B.
    second_user = {
        "email": "seconduser@example.com",
        "username": "seconduser",
        "password": "StrongPassword@123",
        "full_name": "Second User",
    }

    # User B registers.
    register_response = await client.post(
        "/api/v1/auth/register",
        json=second_user,
    )
    assert register_response.status_code == 201

    # User B logs in.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": second_user["email"],
            "password": second_user["password"],
        },
    )
    assert login_response.status_code == 200

    second_user_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # User B attempts to cancel User A's order.
    cancellation_response = await client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=second_user_headers,
    )

    assert cancellation_response.status_code == 404

    # Verify the order still belongs to User A and remains pending.
    order_check = await authenticated_client.get(
        f"/api/v1/orders/{order['id']}"
    )
    assert order_check.status_code == 200
    assert order_check.json()["status"] == "PENDING"

    # Verify inventory remains deducted.
    product_response = await authenticated_client.get(
        f"/api/v1/products/{test_product['id']}"
    )
    assert (
        product_response.json()["stock_quantity"]
        == test_product["stock_quantity"] - 2
    )

@pytest.mark.anyio
async def test_create_order_without_cart(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "123 Test Street, Dehradun, Uttarakhand",
        },
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )
    assert response.json()["status"] == 404

@pytest.mark.anyio
async def test_create_order_with_empty_cart(
    authenticated_client: AsyncClient,
):
    # First, retrieve the cart.
    # This creates an empty cart if one doesn't exist.
    cart_response = await authenticated_client.get(
        "/api/v1/cart"
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []
    assert cart_response.json()["total_items"] == 0

    # Attempt checkout with an empty cart.
    response = await authenticated_client.post(
        "/api/v1/orders",
        json={
            "shipping_address": "123 Test Street, Dehradun, Uttarakhand",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )
    assert response.json()["status"] == 400

@pytest.mark.anyio
async def test_create_order_with_missing_product(
    db: AsyncSession,
    monkeypatch,
):
    # Arrange: simulate a cart item whose product relationship is missing
    user_id = uuid4()

    cart_item = SimpleNamespace(
        product_id=uuid4(),
        product=None,
        quantity=1,
    )

    cart = SimpleNamespace(
        cart_items=[cart_item],
    )

    mock_get_cart = AsyncMock(return_value=cart)

    monkeypatch.setattr(
        order_service.cart_repository,
        "get_cart_with_items",
        mock_get_cart,
    )

    order_data = CreateOrderRequest(
        shipping_address="123 Test Street, Dehradun, Uttarakhand",
    )

    # Act and Assert
    with pytest.raises(ProductNotFoundError):
        await order_service.create_order(
            db=db,
            user_id=user_id,
            order_data=order_data,
        )

    mock_get_cart.assert_awaited_once_with(
        db=db,
        user_id=user_id,
    )

@pytest.mark.anyio
async def test_create_order_with_inactive_product(
    db: AsyncSession,
    monkeypatch,
):
    user_id = uuid4()

    inactive_product = SimpleNamespace(
        id=uuid4(),
        is_active=False,
        stock_quantity=10,
        price=Decimal("799.00"),
    )

    cart_item = SimpleNamespace(
        product_id=inactive_product.id,
        product=inactive_product,
        quantity=1,
    )

    cart = SimpleNamespace(cart_items=[cart_item])

    mock_get_cart = AsyncMock(return_value=cart)

    monkeypatch.setattr(
        order_service.cart_repository,
        "get_cart_with_items",
        mock_get_cart,
    )

    order_data = CreateOrderRequest(
        shipping_address="457 Jane Street, Dehradun, Uttarakhand",
    )

    with pytest.raises(ProductInactiveError):
        await order_service.create_order(
            db=db,
            user_id=user_id,
            order_data=order_data,
        )

    mock_get_cart.assert_awaited_once_with(
        db=db,
        user_id=user_id,
    )

@pytest.mark.anyio
async def test_update_order_status_success(
    db: AsyncSession,
    monkeypatch,
):
    # Arrange
    order_id = uuid4()

    order = SimpleNamespace(
        id=order_id,
        user_id=uuid4(),
        status=OrderStatus.PENDING,
        total_amount=Decimal("1598.00"),
        shipping_address="457 Jane Street, Dehradun, Uttarakhand",
        order_items=[],
        created_at=None,
        updated_at=None,
    )

    mock_get_order = AsyncMock(return_value=order)
    mock_commit = AsyncMock()

    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id",
        mock_get_order,
    )

    monkeypatch.setattr(db, "commit", mock_commit)

    # Act
    result = await order_service.update_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatus.PAID,
    )

    # Assert
    assert order.status == OrderStatus.PAID
    assert result["status"] == OrderStatus.PAID

    mock_get_order.assert_awaited_once_with(
        db=db,
        order_id=order_id,
    )

    mock_commit.assert_awaited_once()

@pytest.mark.anyio
async def test_update_order_status_invalid_transition(
    db: AsyncSession,
    monkeypatch,
):
    # Arrange
    order_id = uuid4()

    order = SimpleNamespace(
        id=order_id,
        user_id=uuid4(),
        status=OrderStatus.PENDING,
        total_amount=Decimal("1598.00"),
        shipping_address="457 Jane Street, Dehradun, Uttarakhand",
        order_items=[],
        created_at=None,
        updated_at=None,
    )

    mock_get_order = AsyncMock(return_value=order)
    mock_commit = AsyncMock()

    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id",
        mock_get_order,
    )

    monkeypatch.setattr(db, "commit", mock_commit)

    # Act & Assert
    with pytest.raises(InvalidOrderStatusTransitionError):
        await order_service.update_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.SHIPPED,
        )

    assert order.status == OrderStatus.PENDING
    mock_commit.assert_not_awaited()

@pytest.mark.anyio
async def test_update_order_status_not_found(
    db: AsyncSession,
    monkeypatch,
):
    order_id = uuid4()

    mock_get_order = AsyncMock(return_value=None)
    mock_commit = AsyncMock()

    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id",
        mock_get_order,
    )

    monkeypatch.setattr(db, "commit", mock_commit)

    with pytest.raises(OrderNotFoundError):
        await order_service.update_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.PAID,
        )

    mock_get_order.assert_awaited_once_with(
        db=db,
        order_id=order_id,
    )

    mock_commit.assert_not_awaited()

@pytest.mark.anyio
@pytest.mark.parametrize(
    "current_status",
    [
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ],
)
async def test_update_terminal_order_status(
    db: AsyncSession,
    monkeypatch,
    current_status: OrderStatus,
):
    order_id = uuid4()

    order = SimpleNamespace(
        id=order_id,
        user_id=uuid4(),
        status=current_status,
        total_amount=Decimal("1598.00"),
        shipping_address="457 Jane Street, Dehradun, Uttarakhand",
        order_items=[],
        created_at=None,
        updated_at=None,
    )

    mock_get_order = AsyncMock(return_value=order)
    mock_commit = AsyncMock()

    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id",
        mock_get_order,
    )

    monkeypatch.setattr(db, "commit", mock_commit)

    with pytest.raises(InvalidOrderStatusTransitionError):
        await order_service.update_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.PENDING,
        )

    assert order.status == current_status
    mock_commit.assert_not_awaited()

@pytest.mark.anyio
async def test_create_order_fails_when_created_order_cannot_be_reloaded(
    db: AsyncSession,
    monkeypatch,
):
    user_id = uuid4()
    product_id = uuid4()

    product = SimpleNamespace(
        id=product_id,
        is_active=True,
        stock_quantity=10,
        price=Decimal("799.00"),
    )

    cart_item = SimpleNamespace(
        product_id=product_id,
        product=product,
        quantity=2,
    )

    cart = SimpleNamespace(cart_items=[cart_item])

    mock_get_cart = AsyncMock(return_value=cart)
    mock_clear_cart = AsyncMock()
    mock_create_order = AsyncMock(
        side_effect=lambda db, order: setattr(order, "id", uuid4())
    )
    mock_reload_order = AsyncMock(return_value=None)
    mock_commit = AsyncMock()
    mock_rollback = AsyncMock()

    monkeypatch.setattr(
        order_service.cart_repository,
        "get_cart_with_items",
        mock_get_cart,
    )
    monkeypatch.setattr(
        order_service.cart_repository,
        "clear_cart",
        mock_clear_cart,
    )
    monkeypatch.setattr(
        order_service.order_repository,
        "create",
        mock_create_order,
    )
    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id_for_user",
        mock_reload_order,
    )
    monkeypatch.setattr(db, "add", lambda item: None)
    monkeypatch.setattr(db, "commit", mock_commit)
    monkeypatch.setattr(db, "rollback", mock_rollback)

    order_data = CreateOrderRequest(
        shipping_address="457 Jane Street, Dehradun, Uttarakhand",
    )

    with pytest.raises(OrderNotFoundError):
        await order_service.create_order(
            db=db,
            user_id=user_id,
            order_data=order_data,
        )

    mock_create_order.assert_awaited_once()
    mock_clear_cart.assert_awaited_once()
    mock_reload_order.assert_awaited_once()
    mock_commit.assert_not_awaited()
    mock_rollback.assert_awaited_once()

@pytest.mark.anyio
async def test_cancel_order_rolls_back_when_commit_fails(
    db: AsyncSession,
    monkeypatch,
):
    user_id = uuid4()
    order_id = uuid4()
    product_id = uuid4()

    product = SimpleNamespace(
        id=product_id,
        stock_quantity=10,
    )

    order_item = SimpleNamespace(
        product=product,
        quantity=2,
    )

    order = SimpleNamespace(
        id=order_id,
        user_id=user_id,
        status=OrderStatus.PENDING,
        order_items=[order_item],
    )

    mock_get_order = AsyncMock(return_value=order)
    mock_commit = AsyncMock(
        side_effect=RuntimeError("Database commit failed")
    )
    mock_rollback = AsyncMock()

    monkeypatch.setattr(
        order_service.order_repository,
        "get_by_id_for_user",
        mock_get_order,
    )
    monkeypatch.setattr(db, "commit", mock_commit)
    monkeypatch.setattr(db, "rollback", mock_rollback)

    with pytest.raises(RuntimeError, match="Database commit failed"):
        await order_service.cancel_order(
            db=db,
            order_id=order_id,
            user_id=user_id,
        )

    mock_get_order.assert_awaited_once()
    mock_commit.assert_awaited_once()
    mock_rollback.assert_awaited_once()