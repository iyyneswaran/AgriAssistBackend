from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from typing import Optional


class UserRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        name: str,
        phone_number: str,
        role: str,
        region: str | None = None,
    ) -> User:
        user = User(
            id=user_id,
            name=name,
            phone_number=phone_number,
            role=role,
            region=region,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: str,
    ) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(
        db: AsyncSession,
        phone_number: str,
    ) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
