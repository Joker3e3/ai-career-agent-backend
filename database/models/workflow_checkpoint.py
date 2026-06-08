from sqlalchemy import Column, DateTime, Integer, String, Text

from database.database import Base
from utils.time import now_utc8


class WorkflowCheckpoint(Base):
    __tablename__ = "workflow_checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)

    workflow_id = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
    )

    current_node = Column(
        String(100),
        nullable=True,
    )

    checkpoint_json = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=now_utc8,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=now_utc8,
        onupdate=now_utc8,
        nullable=False,
    )