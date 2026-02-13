from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    humidity: Mapped[float] = mapped_column(Float, nullable=True)
    soil_moisture: Mapped[float] = mapped_column(Float, nullable=True)

    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
