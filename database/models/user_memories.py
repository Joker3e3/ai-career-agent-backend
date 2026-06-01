from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base
from utils.time import now_utc8

class UserMemory(Base):
    __tablename__ = "user_memories"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    memory_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    content: Mapped[str] = mapped_column(Text)

    source_workflow_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
        onupdate=now_utc8,
    )