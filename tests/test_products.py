from uuid import uuid4
import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_create_product_success(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    """Test successful product creation by an authenticated user."""

    product_payload = {
        "name": "Test Product",
        "description": "A product for testing.",
        "price": 49.99,
        "stock_quantity": 50,
        "category_id": test_category["id"],
        "sku": "TESTSKU123",
    }

    response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == product_payload["name"]
    assert data["description"] == product_payload["description"]
    assert data["price"] == "49.99"
    assert data["stock_quantity"] == 50
    assert data["category_id"] == test_category["id"]
    assert data["sku"] == product_payload["sku"]
    assert data["slug"] == "test-product"
    assert data["is_active"] is True

    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.anyio
async def test_create_product_requires_authentication(
    client: AsyncClient,
):
    """Product creation should reject unauthenticated requests."""

    # Create a category first.
    category_response = await client.post(
        "/api/v1/categories",
        json={
            "name": "Unauthenticated Test Category",
            "description": "Category for authentication testing.",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    # Attempt product creation without an access token.
    product_payload = {
        "name": "Unauthorized Mouse",
        "description": "This product should not be created.",
        "price": "499.00",
        "stock_quantity": 10,
        "category_id": category_id,
        "sku": "UNAUTH-MOUSE-001",
    }

    response = await client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert response.status_code == 401

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 401
    assert data["title"] == "Unauthorized"

@pytest.mark.anyio
@pytest.mark.parametrize(
    "product_payload",
    [
        pytest.param(
            {
                "name": "A",
                "price": "100.00",
                "category_id": "00000000-0000-0000-0000-000000000001",
                "sku": "VALID-SKU-001",
            },
            id="name-too-short",
        ),
        pytest.param(
            {
                "name": "Negative Price Product",
                "price": "-10.00",
                "category_id": "00000000-0000-0000-0000-000000000001",
                "sku": "VALID-SKU-002",
            },
            id="negative-price",
        ),
        pytest.param(
            {
                "name": "Negative Stock Product",
                "price": "100.00",
                "stock_quantity": -5,
                "category_id": "00000000-0000-0000-0000-000000000001",
                "sku": "VALID-SKU-003",
            },
            id="negative-stock",
        ),
        pytest.param(
            {
                "name": "Invalid SKU Product",
                "price": "100.00",
                "category_id": "00000000-0000-0000-0000-000000000001",
                "sku": "AB",
            },
            id="sku-too-short",
        ),
        pytest.param(
            {
                "name": "Missing SKU Product",
                "price": "100.00",
                "category_id": "00000000-0000-0000-0000-000000000001",
            },
            id="missing-sku",
        ),
    ],
)
async def test_create_product_validation_errors(
    authenticated_client: AsyncClient,
    product_payload: dict,
):
    """Product creation should reject invalid product data."""

    response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert response.status_code == 422

@pytest.mark.anyio
async def test_create_product_with_nonexistent_category(
    authenticated_client: AsyncClient,
):
    """Product creation should fail when the category does not exist."""

    # Use a valid UUID that does not belong to an existing category.
    nonexistent_category_id = (
        "00000000-0000-0000-0000-000000000001"
    )

    product_payload = {
        "name": "Product Without Category",
        "description": "This product should not be created.",
        "price": "599.00",
        "stock_quantity": 10,
        "category_id": nonexistent_category_id,
        "sku": "MISSING-CATEGORY-001",
    }

    response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert response.status_code == 404

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert data["detail"] == "Category not found."

@pytest.mark.anyio
async def test_create_product_with_duplicate_sku(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    """Product creation should reject duplicate SKUs."""

    category_id = test_category["id"]

    # Define the first product.
    product_payload = {
        "name": "Wireless Keyboard",
        "description": "First product using this SKU.",
        "price": "1299.00",
        "stock_quantity": 20,
        "category_id": category_id,
        "sku": "DUPLICATE-SKU-001",
    }

    # Create the first product.
    first_response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert first_response.status_code == 201

    # Attempt to create another product with the same SKU.
    duplicate_payload = {
        **product_payload,
        "name": "Mechanical Keyboard",
        "description": "Second product using the same SKU.",
    }

    duplicate_response = await authenticated_client.post(
        "/api/v1/products",
        json=duplicate_payload,
    )

    assert duplicate_response.status_code == 400

    assert duplicate_response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = duplicate_response.json()

    assert data["status"] == 400
    assert data["title"] == "Bad Request"
    assert data["detail"] == "SKU already exists."

@pytest.mark.anyio
async def test_list_products_pagination(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
):
    """Product listing should return correct pagination metadata."""

    category_id = test_category["id"]

    # Create three products.
    for index in range(1, 4):
        response = await authenticated_client.post(
            "/api/v1/products",
            json={
                "name": f"Pagination Product {index}",
                "description": f"Product number {index}.",
                "price": f"{index * 100}.00",
                "stock_quantity": 10,
                "category_id": category_id,
                "sku": f"PAGINATION-SKU-{index:03d}",
            },
        )

        assert response.status_code == 201

    # Request the first page.
    first_response = await client.get(
        "/api/v1/products",
        params={
            "page": 1,
            "size": 2,
        },
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    assert len(first_data["items"]) == 2
    assert first_data["total"] == 3
    assert first_data["page"] == 1
    assert first_data["size"] == 2
    assert first_data["pages"] == 2

    # Request the second page.
    second_response = await client.get(
        "/api/v1/products",
        params={
            "page": 2,
            "size": 2,
        },
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert len(second_data["items"]) == 1
    assert second_data["total"] == 3
    assert second_data["page"] == 2
    assert second_data["size"] == 2
    assert second_data["pages"] == 2

    # Verify that both pages contain different products.
    first_ids = {
        product["id"] for product in first_data["items"]
    }

    second_ids = {
        product["id"] for product in second_data["items"]
    }

    assert first_ids.isdisjoint(second_ids)

@pytest.mark.anyio
@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"page": 0}, id="page-zero"),
        pytest.param({"page": -1}, id="negative-page"),
        pytest.param({"size": 0}, id="size-zero"),
        pytest.param({"size": 101}, id="size-above-maximum"),
    ],
)
async def test_list_products_invalid_pagination(
    client: AsyncClient,
    params: dict,
):
    """Product listing should reject invalid pagination parameters."""

    response = await client.get(
        "/api/v1/products",
        params=params,
    )

    assert response.status_code == 422

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 422
    assert data["title"] == "Unprocessable Content"

@pytest.mark.anyio
async def test_list_products_with_category_and_price_filters(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
):
    category_id = test_category["id"]

    products = [
        {
            "name": "Budget Product",
            "price": "100.00",
            "sku": "FILTER-SKU-001",
        },
        {
            "name": "Midrange Product",
            "price": "500.00",
            "sku": "FILTER-SKU-002",
        },
        {
            "name": "Premium Product",
            "price": "1000.00",
            "sku": "FILTER-SKU-003",
        },
    ]

    for product in products:
        response = await authenticated_client.post(
            "/api/v1/products",
            json={
                **product,
                "description": "Product created for filtering tests.",
                "stock_quantity": 10,
                "category_id": category_id,
            },
        )
        assert response.status_code == 201

    # Filter by category.
    response = await client.get(
        "/api/v1/products",
        params={"category_id": category_id},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert all(
        product["category_id"] == category_id
        for product in data["items"]
    )

    # Filter by minimum price.
    response = await client.get(
        "/api/v1/products",
        params={"min_price": "500.00"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert all(
        float(product["price"]) >= 500
        for product in data["items"]
    )

    # Filter by maximum price.
    response = await client.get(
        "/api/v1/products",
        params={"max_price": "500.00"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert all(
        float(product["price"]) <= 500
        for product in data["items"]
    )

    # Combine category and price filters.
    response = await client.get(
        "/api/v1/products",
        params={
            "category_id": category_id,
            "min_price": "200.00",
            "max_price": "800.00",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Midrange Product"

@pytest.mark.anyio
async def test_list_products_search(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
):
    category_id = test_category["id"]

    products = [
        {
            "name": "Wireless Mechanical Keyboard",
            "sku": "SEARCH-SKU-001",
        },
        {
            "name": "Wireless Gaming Mouse",
            "sku": "SEARCH-SKU-002",
        },
        {
            "name": "USB-C Monitor",
            "sku": "SEARCH-SKU-003",
        },
    ]

    for product in products:
        response = await authenticated_client.post(
            "/api/v1/products",
            json={
                **product,
                "description": "Product created for search testing.",
                "price": "500.00",
                "stock_quantity": 10,
                "category_id": category_id,
            },
        )
        assert response.status_code == 201

    # Search using a complete product name.
    response = await client.get(
        "/api/v1/products",
        params={"search": "Wireless Mechanical Keyboard"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Wireless Mechanical Keyboard"

    # Search using a partial product name.
    response = await client.get(
        "/api/v1/products",
        params={"search": "Wireless"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2

    matching_names = {
        product["name"]
        for product in data["items"]
    }

    assert matching_names == {
        "Wireless Mechanical Keyboard",
        "Wireless Gaming Mouse",
    }

    # Search for a nonexistent product.
    response = await client.get(
        "/api/v1/products",
        params={"search": "Nonexistent Product"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []

@pytest.mark.anyio
@pytest.mark.parametrize(
    ("sort", "expected_names"),
    [
        pytest.param(
            "name",
            ["Alpha Product", "Bravo Product", "Charlie Product"],
            id="name-ascending",
        ),
        pytest.param(
            "-name",
            ["Charlie Product", "Bravo Product", "Alpha Product"],
            id="name-descending",
        ),
        pytest.param(
            "price",
            ["Bravo Product", "Charlie Product", "Alpha Product"],
            id="price-ascending",
        ),
        pytest.param(
            "-price",
            ["Alpha Product", "Charlie Product", "Bravo Product"],
            id="price-descending",
        ),
        pytest.param(
            "created_at",
            ["Alpha Product", "Bravo Product", "Charlie Product"],
            id="created-at-ascending",
        ),
        pytest.param(
            "-created_at",
            ["Charlie Product", "Bravo Product", "Alpha Product"],
            id="created-at-descending",
        ),
    ],
)
async def test_list_products_sorting(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
    sort: str,
    expected_names: list[str],
):
    category_id = test_category["id"]

    products = [
        {
            "name": "Alpha Product",
            "price": "900.00",
            "sku": "SORT-SKU-001",
        },
        {
            "name": "Bravo Product",
            "price": "100.00",
            "sku": "SORT-SKU-002",
        },
        {
            "name": "Charlie Product",
            "price": "500.00",
            "sku": "SORT-SKU-003",
        },
    ]

    for product in products:
        response = await authenticated_client.post(
            "/api/v1/products",
            json={
                **product,
                "description": "Product created for sorting tests.",
                "stock_quantity": 10,
                "category_id": category_id,
            },
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/products",
        params={"sort": sort},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3

    actual_names = [
        product["name"] for product in data["items"]
    ]

    if sort in {"created_at", "-created_at"}:
        timestamps = [
            product["created_at"] for product in data["items"]
        ]

        assert timestamps == sorted(
            timestamps,
            reverse=(sort == "-created_at"),
        )

    else:
        assert actual_names == expected_names

@pytest.mark.anyio
async def test_get_product_by_id_success(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
):
    response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Product Retrieval Test",
            "description": "Testing product retrieval.",
            "price": "750.00",
            "stock_quantity": 15,
            "category_id": test_category["id"],
            "sku": "RETRIEVE-SKU-001",
        },
    )

    assert response.status_code == 201
    created_product = response.json()

    product_id = created_product["id"]

    # Retrieve without authentication.
    response = await client.get(
        f"/api/v1/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Product Retrieval Test"
    assert data["sku"] == "RETRIEVE-SKU-001"
    assert data["price"] == "750.00"
    assert data["stock_quantity"] == 15

@pytest.mark.anyio
async def test_get_product_by_id_not_found(
    client: AsyncClient,
):
    product_id = uuid4()

    response = await client.get(
        f"/api/v1/products/{product_id}"
    )

    assert response.status_code == 404

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert data["detail"] == "Product not found."

@pytest.mark.anyio
async def test_get_product_by_invalid_uuid(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/products/not-a-valid-uuid"
    )

    assert response.status_code == 422

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 422
    assert data["title"] == "Unprocessable Content"

@pytest.mark.anyio
async def test_update_product_success(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    # Create a product.
    create_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Original Product",
            "description": "Original description.",
            "price": "500.00",
            "stock_quantity": 20,
            "category_id": test_category["id"],
            "sku": "UPDATE-SKU-001",
        },
    )

    assert create_response.status_code == 201

    original_product = create_response.json()
    product_id = original_product["id"]

    # Update only the name and price.
    update_response = await authenticated_client.patch(
        f"/api/v1/products/{product_id}",
        json={
            "name": "Updated Product",
            "price": "750.00",
        },
    )

    assert update_response.status_code == 200

    updated_product = update_response.json()

    # Verify updated fields.
    assert updated_product["name"] == "Updated Product"
    assert updated_product["price"] == "750.00"
    assert updated_product["slug"] == "updated-product"

    # Verify unchanged fields.
    assert updated_product["description"] == "Original description."
    assert updated_product["stock_quantity"] == 20
    assert updated_product["sku"] == "UPDATE-SKU-001"
    assert updated_product["category_id"] == test_category["id"]

    # Retrieve again to verify persistence.
    retrieve_response = await authenticated_client.get(
        f"/api/v1/products/{product_id}"
    )

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["name"] == "Updated Product"
    assert retrieve_response.json()["price"] == "750.00"

@pytest.mark.anyio
async def test_update_product_requires_authentication(
    client: AsyncClient,
):
    """Use random UUID because authentication should be checked before
    the endpoint attempts to retrieve a product."""

    response = await client.patch(
        "/api/v1/products/00000000-0000-0000-0000-000000000001",
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

@pytest.mark.anyio
async def test_update_product_with_duplicate_sku(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    # Create the first product.
    first_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "First Product",
            "price": "500.00",
            "stock_quantity": 10,
            "category_id": test_category["id"],
            "sku": "FIRST-SKU-001",
        },
    )
    assert first_response.status_code == 201

    first_product = first_response.json()

    # Create the second product.
    second_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Second Product",
            "price": "750.00",
            "stock_quantity": 15,
            "category_id": test_category["id"],
            "sku": "SECOND-SKU-001",
        },
    )
    assert second_response.status_code == 201

    second_product = second_response.json()

    # Try assigning the second product's SKU to the first product.
    update_response = await authenticated_client.patch(
        f"/api/v1/products/{first_product['id']}",
        json={"sku": second_product["sku"]},
    )

    assert update_response.status_code == 400
    assert update_response.headers["content-type"].startswith(
        "application/problem+json"
    )
    assert update_response.json()["detail"] == "SKU already exists."

    # Verify the original SKU was not changed.
    retrieve_response = await authenticated_client.get(
        f"/api/v1/products/{first_product['id']}"
    )

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["sku"] == "FIRST-SKU-001"

@pytest.mark.anyio
async def test_update_product_with_same_sku(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    # Create a product.
    create_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Original Product",
            "price": "500.00",
            "stock_quantity": 10,
            "category_id": test_category["id"],
            "sku": "SAME-SKU-001",
        },
    )

    assert create_response.status_code == 201
    product = create_response.json()

    # Update the product while retaining its existing SKU.
    update_response = await authenticated_client.patch(
        f"/api/v1/products/{product['id']}",
        json={
            "sku": "SAME-SKU-001",
            "price": "650.00",
        },
    )

    assert update_response.status_code == 200

    updated_product = update_response.json()

    assert updated_product["sku"] == "SAME-SKU-001"
    assert updated_product["price"] == "650.00"

@pytest.mark.anyio
async def test_update_product_with_nonexistent_category(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    # Create a product with a valid category.
    create_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Category Update Test Product",
            "price": "500.00",
            "stock_quantity": 10,
            "category_id": test_category["id"],
            "sku": "CATEGORY-TEST-001",
        },
    )

    assert create_response.status_code == 201
    product = create_response.json()

    # Attempt to update the product with a nonexistent category.
    nonexistent_category_id = str(uuid4())

    update_response = await authenticated_client.patch(
        f"/api/v1/products/{product['id']}",
        json={
            "category_id": nonexistent_category_id,
        },
    )

    assert update_response.status_code == 404
    assert update_response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = update_response.json()
    assert error["title"] == "Not Found"
    assert error["detail"] == "Category not found."

    # Verify that the original category was not changed.
    get_response = await authenticated_client.get(
        f"/api/v1/products/{product['id']}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["category_id"] == test_category["id"]

@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"name": "A"}, id="name-too-short"),
        pytest.param({"price": "-10.00"}, id="negative-price"),
        pytest.param({"stock_quantity": -1}, id="negative-stock"),
        pytest.param({"sku": "AB"}, id="sku-too-short"),
    ],
)
async def test_update_product_validation_errors(
    authenticated_client: AsyncClient,
    test_category: dict,
    payload: dict,
):
    create_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Validation Test Product",
            "price": "500.00",
            "stock_quantity": 10,
            "category_id": test_category["id"],
            "sku": "VALIDATION-001",
        },
    )

    assert create_response.status_code == 201
    product = create_response.json()

    update_response = await authenticated_client.patch(
        f"/api/v1/products/{product['id']}",
        json=payload,
    )

    assert update_response.status_code == 422
    assert update_response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = update_response.json()
    assert error["title"] == "Unprocessable Content"

@pytest.mark.anyio
async def test_update_product_not_found(
    authenticated_client: AsyncClient,
):
    nonexistent_product_id = str(uuid4())

    response = await authenticated_client.patch(
        f"/api/v1/products/{nonexistent_product_id}",
        json={"price": "650.00"},
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()
    assert error["title"] == "Not Found"
    assert error["detail"] == "Product not found."

@pytest.mark.anyio
async def test_update_product_with_invalid_uuid(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.patch(
        "/api/v1/products/invalid-uuid",
        json={"price": "650.00"},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()
    assert error["title"] == "Unprocessable Content"

@pytest.mark.anyio
async def test_delete_product_success(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    # Create a product.
    create_response = await authenticated_client.post(
        "/api/v1/products",
        json={
            "name": "Product To Delete",
            "price": "500.00",
            "stock_quantity": 10,
            "category_id": test_category["id"],
            "sku": "DELETE-TEST-001",
        },
    )

    assert create_response.status_code == 201
    product = create_response.json()

    # Delete the product.
    delete_response = await authenticated_client.delete(
        f"/api/v1/products/{product['id']}"
    )

    assert delete_response.status_code == 200

    deleted_product = delete_response.json()

    assert deleted_product["id"] == product["id"]
    assert deleted_product["is_active"] is False

    # Verify that the product is no longer in the active catalog.
    list_response = await authenticated_client.get(
        "/api/v1/products"
    )

    assert list_response.status_code == 200

    product_ids = [
        item["id"] for item in list_response.json()["items"]
    ]

    assert product["id"] not in product_ids

@pytest.mark.anyio
async def test_delete_product_requires_authentication(
    client: AsyncClient,
):
    response = await client.delete(
        f"/api/v1/products/{uuid4()}"
    )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()
    assert error["title"] == "Unauthorized"

@pytest.mark.anyio
async def test_delete_product_not_found(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.delete(
        f"/api/v1/products/{uuid4()}"
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()
    assert error["title"] == "Not Found"
    assert error["detail"] == "Product not found."

@pytest.mark.anyio
async def test_delete_product_is_idempotent(
    authenticated_client: AsyncClient,
    test_category: dict,
):
    product_payload = {
        "name": "Idempotent Delete Product",
        "description": "Testing repeated soft deletion.",
        "price": "499.99",
        "stock_quantity": 10,
        "category_id": test_category["id"],
        "sku": "IDEMPOTENT-001",
    }

    create_response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # First deletion
    first_delete = await authenticated_client.delete(
        f"/api/v1/products/{product_id}"
    )
    assert first_delete.status_code == 200
    assert first_delete.json()["is_active"] is False

    # Second deletion
    second_delete = await authenticated_client.delete(
        f"/api/v1/products/{product_id}"
    )
    assert second_delete.status_code == 200
    assert second_delete.json()["is_active"] is False

@pytest.mark.anyio
async def test_get_soft_deleted_product(
    client: AsyncClient,
    authenticated_client: AsyncClient,
    test_category: dict,
):
    product_payload = {
        "name": "Soft Deleted Product",
        "description": "Testing retrieval after soft deletion.",
        "price": "299.99",
        "stock_quantity": 5,
        "category_id": test_category["id"],
        "sku": "SOFT-DELETE-001",
    }

    create_response = await authenticated_client.post(
        "/api/v1/products",
        json=product_payload,
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Soft-delete the product.
    delete_response = await authenticated_client.delete(
        f"/api/v1/products/{product_id}"
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False

    # Attempt to retrieve the deleted product.
    get_response = await client.get(
        f"/api/v1/products/{product_id}"
    )

    # Current implementation still exposes the inactive product.
    assert get_response.status_code == 404

    assert get_response.headers["Content-type"].startswith(
        "application/problem+json"
    )

    error = get_response.json()
    assert error["title"] == "Not Found"
    assert error["detail"] == "Product not found."