from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.conversation import Conversation
from typing import Optional, List


class ConversationRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        metadata: dict | None = None,
    ) -> Conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            extra_metadata=metadata or {},
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        conversation_id: str,
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: str,
    ) -> List[Conversation]:
        result = await db.execute(
            select(Conversation).where(Conversation.user_id == user_id)
        )
        return result.scalars().all()
