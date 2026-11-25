from uuid import uuid4
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.exceptions.product import InsufficientStockError

@pytest.mark.anyio
async def test_get_cart_creates_cart_for_new_user(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.get("/api/v1/cart")

    assert response.status_code == 200

    data = response.json()

    # Cart should be created automatically.
    assert "id" in data
    assert "user_id" in data

    # A newly created cart should be empty
    assert data["items"] == []
    assert data["total_items"] == 0
    assert data["total_price"] == "0.00"

    # Cart timestamps should be present.
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.anyio
async def test_add_product_to_cart_success(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Cart should contain one item.
    assert len(data["items"]) == 1

    item = data["items"][0]

    # Verify cart item details.
    assert item["product"]["id"] == test_product["id"]
    assert item["quantity"] == 2

    # Verify calculated totals.
    assert data["total_items"] == 2
    assert data["total_price"] == "1598.00"

@pytest.mark.anyio
async def test_adding_same_product_increases_quantity(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # First addition: quantity 2.
    first_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert first_response.status_code == 200

    # Second additon: quantity 3.
    second_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 3,
        },
    )

    assert second_response.status_code == 200

    data = second_response.json()

    # Same product should remain a single cart item.
    assert len(data["items"]) == 1

    # Quantities should be combined.
    assert data["items"][0]["quantity"] == 5

    # Verify updated totals.
    assert data["total_items"] == 5
    assert data["total_price"] == "3995.00"

@pytest.mark.anyio
async def test_add_product_exceeding_stock_returns_error(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 51,
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    # Verify standardized error response.
    error = response.json()
    assert error["status"] == 400
    assert error["code"] == "INSUFFICIENT_STOCK"

    # Failed addition must not create a cart item.
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200

    cart = cart_response.json()
    assert cart["items"] == []
    assert cart["total_items"] == 0

@pytest.mark.anyio
async def test_add_inactive_product_returns_error(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Deactivate the product.
    update_response = await authenticated_client.patch(
        f"/api/v1/products/{test_product['id']}",
        json={"is_active": False},
    )

    assert update_response.status_code == 200

    # Attempt to add the inactive product.
    response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 1,
        },
    )

    assert response.status_code == 400

    error = response.json()
    assert error["code"] == "PRODUCT_INACTIVE"

    # Verify that no item was added.
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []

@pytest.mark.anyio
async def test_add_product_with_zero_quantity_returns_validation_error(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 0,
        },
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["status"] == 422
    assert error["code"] == "VALIDATION_ERROR"

    # Cart should remain empty.
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []

@pytest.mark.anyio
async def test_update_cart_item_quantity_success(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # First add two units to the cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity" : 2,
        },
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["items"][0]["id"]

    # Update the quantity to four.
    update_response = await authenticated_client.patch(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 4},
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == cart_item_id
    assert data["items"][0]["quantity"] == 4

    # Verify recalculated totals
    assert data["total_items"] == 4
    assert data["total_price"] == "3196.00"

@pytest.mark.anyio
async def test_update_cart_item_quantity_to_zero_removes_item(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Add a product to the cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["items"][0]["id"]

    # Set quantity to zero.
    update_response = await authenticated_client.patch(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 0},
    )

    assert update_response.status_code == 200

    data = update_response.json()

    # The item should be removed.
    assert data["items"] == []

    # Cart totals should reset.
    assert data["total_items"] == 0
    assert data["total_price"] == "0.00"

@pytest.mark.anyio
async def test_remove_cart_item_success(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Add a product to the cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 3,
        },
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["items"][0]["id"]

    # Remove the cart item.
    delete_response = await authenticated_client.delete(
        f"/api/v1/cart/items/{cart_item_id}"
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    # Verify that the item has been removed.
    assert data["items"] == []
    assert data["total_items"] == 0
    assert data["total_price"] == "0.00"

@pytest.mark.anyio
async def test_remove_nonexistent_cart_item_returns_404(
    authenticated_client: AsyncClient
):
    nonexistent_item_id = uuid4()

    response = await authenticated_client.delete(
        f"/api/v1/cart/items/{nonexistent_item_id}",
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()
    assert error["status"] == 404

@pytest.mark.anyio
async def test_user_cannot_modify_another_users_cart_items(
    authenticated_client: AsyncClient,
    client: AsyncClient,
    test_product: dict,
):
    # User A adds a product to their cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert add_response.status_code == 200

    cart_item_id = add_response.json()["items"][0]["id"]

    # Register User B.
    second_user_payload = {
        "email": "seconduser@example.com",
        "username": "seconduser",
        "password": "StrongPassword@123",
        "full_name": "Second User",
    }

    register_response = await client.post(
        "/api/v1/auth/register",
        json=second_user_payload,
    )

    assert register_response.status_code == 201

    # Authenticaate User B.
    login_response = await client.post(
        "api/v1/auth/login",
        json={
            "email": second_user_payload["email"],
            "password": second_user_payload["password"],
        },
    )

    assert login_response.status_code == 200

    second_user_headers = {
        "Authorization": f"Bearer {login_response.json()["access_token"]}"
    }

    # user B attempts to update User A's cart item.
    update_response = await client.patch(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 4},
        headers=second_user_headers,
    )

    assert update_response.status_code == 404

    # User A should still have the original caart item.
    owner_cart_response = await authenticated_client.get(
        "/api/v1/cart"
    )

    assert owner_cart_response.status_code == 200

    owner_cart = owner_cart_response.json()

    assert len(owner_cart["items"]) == 1
    assert owner_cart["items"][0]["id"] == cart_item_id
    assert owner_cart["items"][0]["quantity"] == 2

@pytest.mark.anyio
async def test_users_have_separate_carts(
    authenticated_client: AsyncClient,
    client: AsyncClient,
    test_product: dict,
):
    # User A adds a product to their cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 3,
        },
    )

    assert add_response.status_code == 200

    user_a_cart = add_response.json()

    # Register User B.
    second_user_payload = {
        "email": "cartuser2@example.com",
        "username": "cartuser2",
        "password": "StrongPassword@123",
        "full_name": "Cart User Two",
    }

    register_response = await client.post(
        "/api/v1/auth/register",
        json=second_user_payload,
    )

    assert register_response.status_code == 201

    # Authenticate User B.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": second_user_payload["email"],
            "password": second_user_payload["password"],
        },
    )

    assert login_response.status_code == 200

    user_b_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # User B retrieves their cart.
    user_b_response = await client.get(
        "/api/v1/cart",
        headers=user_b_headers,
    )

    assert user_b_response.status_code == 200

    user_b_cart = user_b_response.json()

    # Both users must have different carts.
    assert user_a_cart["id"] != user_b_cart["id"]
    assert user_a_cart["user_id"] != user_b_cart["user_id"]

    # User B's cart must be empty.
    assert user_b_cart["items"] == []
    assert user_b_cart["total_items"] == 0
    assert user_b_cart["total_price"] == "0.00"

@pytest.mark.anyio
async def test_clear_cart_removes_all_items(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Add a product to the cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 3,
        },
    )

    assert add_response.status_code == 200

    cart_before_clear = add_response.json()

    assert len(cart_before_clear["items"]) == 1
    assert cart_before_clear["total_items"] == 3

    # Clear the cart.
    clear_response = await authenticated_client.delete(
        "/api/v1/cart"
    )

    assert clear_response.status_code == 200

    cart_after_clear = clear_response.json()

    # The cart should still exist.
    assert cart_after_clear["id"] == cart_before_clear["id"]
    assert cart_after_clear["user_id"] == cart_before_clear["user_id"]

    # All items and totals should be cleared.
    assert cart_after_clear["items"] == []
    assert cart_after_clear["total_items"] == 0
    assert cart_after_clear["total_price"] == "0.00"

@pytest.mark.anyio
async def test_update_cart_item_quantity_exceeding_stock_returns_error(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # Add a product to the cart.
    add_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 2,
        },
    )

    assert add_response.status_code == 200

    cart = add_response.json()
    cart_item_id = cart["items"][0]["id"]

    # Attempt to update quantity beyond available stock.
    update_response = await authenticated_client.patch(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": test_product["stock_quantity"] + 1},
    )

    assert update_response.status_code == 400

    error = update_response.json()

    assert error["status"] == 400
    assert error["code"] == "INSUFFICIENT_STOCK"

    # Verify the original quantity remains unchanged.
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200

    updated_cart = cart_response.json()

    assert updated_cart["items"][0]["quantity"] == 2
    assert updated_cart["total_items"] == 2

@pytest.mark.anyio
async def test_adding_existing_product_beyond_combined_stock_returns_error(
    authenticated_client: AsyncClient,
    test_product: dict,
):
    # First addition: 30 units
    first_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 30,
        },
    )

    assert first_response.status_code == 200

    # Second addition: 21 units
    second_response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 21,
        },
    )

    assert second_response.status_code == 400

    error = second_response.json()

    assert error["status"] == 400
    assert error["code"] == "INSUFFICIENT_STOCK"

    # The original quantity must remain unchanged
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200

    cart = cart_response.json()

    assert len(cart["items"])  == 1
    assert cart["items"][0]["quantity"] == 30
    assert cart["total_items"] == 30

@pytest.mark.anyio
async def test_add_nonexistent_product_returns_404(
    authenticated_client: AsyncClient,
):
    import uuid

    nonexistent_product_id = str(uuid.uuid4())

    response = await authenticated_client.post(
        "/api/v1/cart/items",
        json={
            "product_id": nonexistent_product_id,
            "quantity": 1,
        },
    )

    assert response.status_code == 404

    error = response.json()

    assert error["status"] == 404
    assert error["code"] == "PRODUCT_NOT_FOUND"

    # Verify that no item was added.
    cart_response = await authenticated_client.get("/api/v1/cart")

    assert cart_response.status_code == 200

    cart = cart_response.json()

    assert cart["items"] == []
    assert cart["total_items"] == 0

@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method", "url", "payload"),
    [
        ("GET", "/api/v1/cart", None),
        (
            "POST",
            "/api/v1/cart/items",
            {
                "product_id": "00000000-0000-0000-0000-000000000001",
                "quantity": 1,
            },
        ),
        (
            "PATCH",
            "/api/v1/cart/items/00000000-0000-0000-0000-000000000001",
            {"quantity": 2},
        ),
        (
            "DELETE",
            "/api/v1/cart/items/00000000-0000-0000-0000-000000000001",
            None,
        ),
        ("DELETE", "/api/v1/cart", None),
    ],
)
async def test_cart_endpoints_require_authentication(
    client: AsyncClient,
    method: str,
    url: str,
    payload: dict | None,
):
    response = await client.request(
        method,
        url,
        json=payload,
    )

    assert response.status_code == 401