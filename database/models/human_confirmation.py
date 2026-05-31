from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base
from utils.time import now_utc8


class HumanConfirmation(Base):
    __tablename__ = "human_confirmations"

    id: Mapped[int] = mapped_column(primary_key=True)

    confirmation_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    workflow_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    actor_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    user_action: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    payload_snapshot: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
