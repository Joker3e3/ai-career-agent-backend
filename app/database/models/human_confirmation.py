from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class HumanConfirmation(Base):

    __tablename__ = "human_confirmations"

    id: Mapped[int] = mapped_column(primary_key=True)

    confirmation_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    workflow_id: Mapped[str] = mapped_column(
        String(255),
        index=True
    )

    action_type: Mapped[str] = mapped_column(
        String(100)
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )

    user_action: Mapped[str] = mapped_column(
        String(50),
        default=""
    )

    message: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )