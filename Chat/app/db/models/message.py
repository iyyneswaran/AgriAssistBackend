from sqlalchemy import String, DateTime, ForeignKey, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.db.base import Base


class MessageSender(str, enum.Enum):
    USER = "USER"
    AI = "AI"
    SYSTEM = "SYSTEM"


class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    VOICE = "VOICE"


class Message(Base):
    __tablename__ = "ai_chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    conversationId: Mapped[str] = mapped_column(
        String,
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    sender: Mapped[MessageSender] = mapped_column(Enum(MessageSender, name="MessageSender"), nullable=False)
    messageType: Mapped[MessageType] = mapped_column(Enum(MessageType, name="MessageType"), nullable=False)

    textContent: Mapped[str] = mapped_column(Text, nullable=True)
    filePath: Mapped[str] = mapped_column(String, nullable=True)
    
    fileName: Mapped[str] = mapped_column(String, nullable=True)
    mimeType: Mapped[str] = mapped_column(String, nullable=True)
    fileSizeBytes: Mapped[int] = mapped_column(Integer, nullable=True)

    createdAt: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
