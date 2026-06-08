from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base
from utils.time import now_utc8


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    node_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
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

    input_tokens: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
    )
