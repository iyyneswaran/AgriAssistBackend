from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings
from app.db.base import Base


# IMPORTANT:
# Neon/PostgreSQL async URL must use:
# postgresql+asyncpg://
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)


engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
