from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base import Base


class VoiceLog(Base):
    __tablename__ = "voice_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    conversation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )

    input_audio_path: Mapped[str] = mapped_column(String, nullable=False)
    output_audio_path: Mapped[str] = mapped_column(String, nullable=True)

    transcript: Mapped[str] = mapped_column(String, nullable=True)

    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
