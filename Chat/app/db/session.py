import ssl as ssl_module

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
# Also strip ?ssl=require / &ssl=require because asyncpg
# does NOT understand it as a query-string param.
DATABASE_URL = (
    settings.DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("?ssl=require", "")
    .replace("&ssl=require", "")
)

# asyncpg needs a real SSL context for Neon's TLS requirement
ssl_context = ssl_module.create_default_context()


engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": ssl_context},
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


from app.db.models.user import User  # noqa: E402, F401
from app.db.models.conversation import Conversation  # noqa: E402, F401
from app.db.models.message import Message  # noqa: E402, F401
from app.db.models.sensor_data import SensorData  # noqa: E402, F401
from app.db.models.voice_log import VoiceLog  # noqa: E402, F401

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
