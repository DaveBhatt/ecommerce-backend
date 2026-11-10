from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Asynchronous database configuration
def get_async_database_url(database_url: str) -> str:
    """Convert a PostgreSQL URL to use the asyncpg driver."""

    url = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        raise ValueError("Only PostgreSQL databases are supported.")

    return url.set(
        drivername="postgresql+asyncpg"
    ).render_as_string(hide_password=False)

ASYNC_DATABASE_URL = get_async_database_url(settings.DATABASE_URL)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)
