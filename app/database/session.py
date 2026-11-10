from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import AsyncSessionLocal

# Asynchronous database dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide asynchronous database session
    """

    async with AsyncSessionLocal() as db:
        yield db
