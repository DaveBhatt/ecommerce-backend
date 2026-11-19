import pytest
from httpx import AsyncClient

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.core.config import settings

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

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

@pytest.mark.anyio
async def test_get_current_user_requires_authentication(
    client: AsyncClient,
):
    """Protected endpoint should reject requests without authentication."""

    response = await client.get("api/v1/users/me")

    assert response.status_code == 401

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 401
    assert data["title"] == "Unauthorized"
    assert data["instance"] == "/api/v1/users/me"

@pytest.mark.anyio
async def test_get_current_user_rejects_invalid_token(
    client: AsyncClient,
):
    """Protected endpoint should reject an invalid JWT."""

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 401

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 401
    assert data["detail"] == "Invalid authentication credentials"

@pytest.mark.anyio
async def test_login_user_success(
    client: AsyncClient,
):
    """Test successful login returns a JWT access token."""

    user_payload = {
        "email": "loginuser@example.com",
        "username": "loginuser",
        "password": "StrongPassword123",
        "full_name": "Login User",
    }

    # Register the user first
    register_respone = await client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert register_respone.status_code == 201

    # Login using the registered credentials.
    login_reponse = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user_payload["email"],
            "password": user_payload["password"],
        },
    )

    assert login_reponse.status_code == 200

    data = login_reponse.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_user_invalid_password(client: AsyncClient):
    """Test login with an incorrect password."""

    user_payload = {
        "email": "invalidlogin@example.com",
        "username": "invalidlogin",
        "password": "StrongPassword123",
        "full_name": "Invalid Login",
    }

    # Register the user.
    register_response = await client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert register_response.status_code == 201

    # Attempt login with an incorrect password.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user_payload["email"],
            "password": "WrongPassword123",
        },
    )

    assert login_response.status_code == 401

    assert login_response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = login_response.json()

    assert data["status"] == 401
    assert data["detail"] == "Invalid email or password"

@pytest.mark.anyio
async def test_login_user_nonexistent_email(client: AsyncClient):
    """Test login with an email that is not registered."""

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 401

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 401
    assert data["detail"] == "Invalid email or password"

@pytest.mark.anyio
async def test_get_current_user_rejects_expired_token(client: AsyncClient):
    """Test that an expired JWT cannot access protected endpoints."""

    expired_payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 401
    assert data["detail"] == "Invalid authentication credentials"

@pytest.mark.anyio
async def test_inactive_user_cannot_access_protected_endpoint(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test that an inactive user cannot access protected endpoints."""

    user_payload = {
        "email": "inactive@example.com",
        "username": "inactiveuser",
        "password": "StrongPassword123",
        "full_name": "Inactive User",
    }

    # Register the user.
    register_response = await client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    # Deactivate the user directly in the test database.
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=False)
    )

    await db.flush()

    # Login to obtain a valid access token.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user_payload["email"],
            "password": user_payload["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Attempt to access a protected endpoint.
    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["status"] == 403
    assert data["detail"] == "Inactive user"

@pytest.mark.anyio
async def test_authenticated_user_can_access_profile(client: AsyncClient):
    """Test that an authenticated user can access their own profile."""

    user_payload = {
        "email": "profile@example.com",
        "username": "profileuser",
        "password": "StrongPassword123",
        "full_name": "Profile User",
    }

    # Register the user.
    register_response = await client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert register_response.status_code == 201

    # Login and obtain access token.
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user_payload["email"],
            "password": user_payload["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Access the authenticated user's profile.
    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == user_payload["email"]
    assert data["username"] == user_payload["username"]
    assert data["full_name"] == user_payload["full_name"]
    assert data["is_active"] is True
