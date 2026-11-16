import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_validation_error_returns_problem_details(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "password": "StrongPassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    data = response.json()

    assert data["type"] == "about:blank"
    assert data["title"] == "Unprocessable Content"
    assert data["status"] == 422
    assert data["detail"] == "Request validation failed."
    assert data["instance"] == "/api/v1/auth/register"
    assert data["code"] == "VALIDATION_ERROR"

    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0

    # Ensure submitted values are not exposed.
    for error in data["errors"]:
        assert "input" not in error
        assert "ctx" not in error

@pytest.mark.anyio
async def test_not_found_returns_problem_details(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/this-route-does-not-exist"
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    assert response.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Not Found",
        "instance": "/api/v1/this-route-does-not-exist",
        "code": "HTTP_ERROR",
    }