import pytest

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.database.base import Base
from app.database.session import get_async_db
from app.main import app

# Import all models so SQLAlchemy registers their tables without shadowing the
# FastAPI instance imported above.
from app import models


@pytest.fixture
async def test_engine(anyio_backend):
    if not settings.TEST_DATABASE_URL:
        raise RuntimeError("TEST_DATABASE_URL is not configured.")

    test_url = make_url(settings.TEST_DATABASE_URL)
    development_url = make_url(settings.DATABASE_URL)

    # Safety check: never run tests against development database.
    if test_url.database == development_url.database:
        raise RuntimeError("Test database must be different from development database.")

    # Ensure tests connect to the expected PostgreSQL server.
    if (
        test_url.host != development_url.host
        or (test_url.port or 5432) != (development_url.port or 5432)
    ):
        raise RuntimeError(
            "Test database must use the same PostgreSQL server as the development database."
        )

    if test_url.database != "ecommerce_test_db":
        raise RuntimeError("Unexpected test database. Expected ecommerce_test_db.")

    async_database_url = test_url.set(
        drivername="postgresql+asyncpg"
    ).render_as_string(hide_password=False)

    engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
    )

    try:
        # Verify the actual database connection
        async with engine.connect() as connection:
            database_name = await connection.execute(
                text("SELECT current_database()")
            )

            database_name = database_name.scalar_one()

            if database_name != "ecommerce_test_db":
                raise RuntimeError(f"Connected to unexpected database: {database_name}")

        # Create all registered model tables.
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        yield engine

        # Clean up the dedicated test database.
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)

    finally:
        await engine.dispose()


@pytest.fixture
async def db(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        TestingSessionLocal = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with TestingSessionLocal() as session:
            try:
                yield session
            finally:
                await transaction.rollback()

@pytest.fixture
async def client(db):
    async def override_get_async_db():
        yield db

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_async_db] = override_get_async_db

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

@pytest.fixture
async def registered_user(client):
    """Register and return a test user."""

    user_payload = {
        "email": "fixtureuser@example.com",
        "username": "fixtureuser",
        "password": "StrongPassword@123",
        "full_name": "Fixture User",
    }

    response = await client.post(
        "/api/v1/auth/register",
        json=user_payload,
    )

    assert response.status_code == 201

    return user_payload

@pytest.fixture
async def auth_headers(client, registered_user):
    """Authenticate the registered user and return the JWT headers."""

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }

@pytest.fixture
async def authenticated_client(client, auth_headers):
    """Return an HTTP client with authentication headers set for the registered user."""

    client.headers.update(auth_headers)

    return client

@pytest.fixture
def category_payload():
    return {
        "name": "Fixture Electronics",
        "description": "Category created by a reusable fixture.",
    }


@pytest.fixture
async def test_category(client, category_payload):
    response = await client.post(
        "/api/v1/categories",
        json=category_payload,
    )
    assert response.status_code == 201
    return response.json()