import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration"""

    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "StrongPassword123",
        "full_name": "Test User",
    }

    response = await client.post("/api/v1/auth/register", json=payload,)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert data["full_name"] == payload["full_name"]

    assert "id" in data
    assert data["is_active"] is True
    assert data["is_superuser"] is False

    assert "password" not in data
    assert "hashed_password" not in data

@pytest.mark.anyio
async def test_register_user_duplicate_email(client: AsyncClient):
    """Test registration with asn already registered email."""

    first_user = {
        "email": "duplicate@example.com",
        "username": "firstuser",
        "password": "StrongPassword123",
        "full_name": "First User",
    }

    second_user = {
        "email": "duplicate@example.com",
        "username": "seconduser",
        "password": "StrongPassword123",
        "full_name": "Second User",
    }

    # Register the first user.
    first_response = await client.post(
        "/api/v1/auth/register", json=first_user,
    )

    assert first_response.status_code == 201

    # Attempt to register another user with the same email.
    second_response = await client.post(
        "/api/v1/auth/register", json=second_user,
    )

    assert second_response.status_code == 409

    assert second_response.headers["content-type"].startswith(
        "application/problem+json"
    )
    """
    RFC 9457 uses application/problem+json
    This tells API clients that the response contains a Problem Details
    document rather than an ordinary JSON success reponse.
    """
    assert second_response.json() == {
        "type": "about:blank",
        "title": "Conflict",
        "status": 409,
        "detail": "Email already registered",
        "instance": "/api/v1/auth/register",
        "code": "HTTP_ERROR",
    }