from uuid import uuid4
import pytest

from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_category_success(
    client: AsyncClient,
):
    payload = {
        "name": "Electronics",
        "description": "Electronic devices and accessories.",
    }

    response = await client.post(
        "/api/v1/categories",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["slug"] == "electronics"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.anyio
async def test_create_category_duplicate_name(
    client: AsyncClient,
    test_category,
):
    response = await client.post(
        "/api/v1/categories",
        json={
            "name": test_category["name"],
            "description": "Duplicate category.",
        },
    )

    assert response.status_code == 400

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 400
    assert data["detail"] == "Category already exists."


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "A",
            "description": "Valid description.",
        },
        {
            "name": "X" * 101,
            "description": "Valid description.",
        },
        {
            "name": "Electronics",
            "description": "D" * 501,
        },
        {
            "description": "Missing category name.",
        },
    ],
    ids=[
        "name-too-short",
        "name-too-long",
        "description-too-long",
        "missing-name",
    ],
)
async def test_create_category_validation_errors(
    client: AsyncClient,
    payload: dict,
):
    response = await client.post(
        "/api/v1/categories",
        json=payload,
    )

    assert response.status_code == 422

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 422
    assert data["title"] == "Unprocessable Content"
    assert data["detail"] == "Request validation failed."

async def test_list_categories_success(client, test_category):
    response = await client.get("/api/v1/categories")

    assert response.status_code == 200

    categories = response.json()

    assert isinstance(categories, list)

    category = next(
        (
            item for item in categories
            if item["id"] == test_category["id"]
        ),
        None,
    )

    assert category is not None
    assert category["name"] == test_category["name"]
    assert category["slug"] == test_category["slug"]
    assert category["is_active"] is True


async def test_get_category_by_id_success(client, test_category):
    category_id = test_category["id"]

    response = await client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 200

    category = response.json()

    assert category["id"] == category_id
    assert category["name"] == test_category["name"]
    assert category["slug"] == test_category["slug"]
    assert category["description"] == test_category["description"]
    assert category["is_active"] is True


async def test_get_category_by_id_not_found(client):
    category_id = str(uuid4())

    response = await client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Not Found"
    assert error["detail"] == "Category not found"


async def test_get_category_by_invalid_uuid(client):
    response = await client.get(
        "/api/v1/categories/invalid-uuid"
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Unprocessable Content"

async def test_update_category_success(client, test_category):
    category_id = test_category["id"]

    response = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={
            "name": "Updated Electronics",
            "description": "Updated category description.",
        },
    )

    assert response.status_code == 200

    updated_category = response.json()

    assert updated_category["id"] == category_id
    assert updated_category["name"] == "Updated Electronics"
    assert updated_category["slug"] == "updated-electronics"
    assert updated_category["description"] == "Updated category description."
    assert updated_category["is_active"] is True

    # Verify persistence through a separate GET request.
    get_response = await client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Updated Electronics"


async def test_update_category_name_with_duplicate(
    client,
    test_category,
):
    existing_category = await client.post(
        "/api/v1/categories",
        json={
            "name": "Books",
            "description": "Books category.",
        },
    )

    assert existing_category.status_code == 201

    category_id = test_category["id"]

    response = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={
            "name": "Books",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Bad Request"
    assert error["detail"] == "Category already exists."


async def test_update_category_not_found(client):
    category_id = str(uuid4())

    response = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={
            "name": "Updated Category",
        },
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Not Found"
    assert error["detail"] == "Category not found"


async def test_update_category_with_invalid_uuid(client):
    response = await client.patch(
        "/api/v1/categories/invalid-uuid",
        json={
            "name": "Updated Category",
        },
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Unprocessable Content"

async def test_delete_category_success(client, test_category):
    category_id = test_category["id"]

    response = await client.delete(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    # Soft-deleted categories should not appear in the listing.
    list_response = await client.get("/api/v1/categories")

    assert list_response.status_code == 200

    category_ids = [
        category["id"]
        for category in list_response.json()
    ]

    assert category_id not in category_ids


async def test_delete_category_not_found(client):
    category_id = str(uuid4())

    response = await client.delete(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Not Found"
    assert error["detail"] == "Category not found"


async def test_delete_category_with_invalid_uuid(client):
    response = await client.delete(
        "/api/v1/categories/invalid-uuid"
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Unprocessable Content"


async def test_delete_category_is_idempotent(client, test_category):
    category_id = test_category["id"]

    first_response = await client.delete(
        f"/api/v1/categories/{category_id}"
    )

    second_response = await client.delete(
        f"/api/v1/categories/{category_id}"
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 204

async def test_get_soft_deleted_category(client, test_category):
    category_id = test_category["id"]

    # Soft-delete the category.
    delete_response = await client.delete(
        f"/api/v1/categories/{category_id}"
    )

    assert delete_response.status_code == 204

    # Public retrieval should not expose inactive categories.
    response = await client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    error = response.json()

    assert error["title"] == "Not Found"
    assert error["detail"] == "Category not found"