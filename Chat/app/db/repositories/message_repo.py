from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.message import Message, MessageRole
from typing import List, Optional


class MessageRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        message_id: str,
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            extra_metadata=metadata or {},
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        message_id: str,
    ) -> Optional[Message]:
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 50,
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
