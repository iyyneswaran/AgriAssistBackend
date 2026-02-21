from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.db.base import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class Conversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    userId: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    fieldId: Mapped[str] = mapped_column(String, nullable=True)
    cropAssignmentId: Mapped[str] = mapped_column(String, nullable=True)

    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)

    startedAt: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    endedAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)
