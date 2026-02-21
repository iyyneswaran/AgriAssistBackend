from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    FARMER = "FARMER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.FARMER)
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    crop_type: Mapped[str] = mapped_column(String(100), nullable=True)
    land_size: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
