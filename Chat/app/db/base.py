from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Base.metadata knows about them
# These imports MUST be after Base is defined to avoid circular imports
from app.db.models.user import User  # noqa: E402, F401
from app.db.models.conversation import Conversation  # noqa: E402, F401
from app.db.models.message import Message  # noqa: E402, F401
from app.db.models.sensor_data import SensorData  # noqa: E402, F401
from app.db.models.voice_log import VoiceLog  # noqa: E402, F401
