from datetime import datetime

from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base
from app.utils.time import now_utc8


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    step_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    tool_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    tool_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    input_summary: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    output_summary: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
    )
