# app/db/repositories/scheme_repo.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.db.models.scheme_log import SchemeLog


class SchemeRepository:

    async def log_recommendation(
        self,
        db: AsyncSession,
        user_id: UUID,
        scheme_id: UUID,
        title: str,
        similarity_score: float,
        final_score: float,
    ) -> SchemeLog:

        log = SchemeLog(
            user_id=user_id,
            scheme_id=scheme_id,
            title=title,
            similarity_score=similarity_score,
            final_score=final_score,
            interaction_type="recommended",
        )

        db.add(log)
        await db.commit()
        await db.refresh(log)

        return log

    async def update_interaction(
        self,
        db: AsyncSession,
        log_id: UUID,
        interaction_type: str,
    ) -> SchemeLog:

        result = await db.execute(
            select(SchemeLog).where(SchemeLog.id == log_id)
        )

        log = result.scalar_one_or_none()

        if not log:
            return None

        log.interaction_type = interaction_type

        await db.commit()
        await db.refresh(log)

        return log

    async def get_user_logs(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[SchemeLog]:

        result = await db.execute(
            select(SchemeLog)
            .where(SchemeLog.user_id == user_id)
            .order_by(SchemeLog.created_at.desc())
        )

        return result.scalars().all()