import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SchemeLog(Base):
    """
    Logs scheme recommendations served to users.
    """

    __tablename__ = "scheme_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scheme_id = Column(UUID(as_uuid=True), nullable=False)

    title = Column(String, nullable=False)

    similarity_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)

    interaction_type = Column(
        String,
        nullable=True
    )
    # Possible values:
    # recommended
    # viewed
    # clicked
    # applied

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship (optional if user model already has backref)
    user = relationship("User")