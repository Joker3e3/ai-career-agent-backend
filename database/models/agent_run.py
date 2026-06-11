from datetime import datetime

from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base
from utils.time import now_utc8


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    run_type: Mapped[str] = mapped_column(
        String(100),
        default="career_analysis",
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

    jd_text: Mapped[str] = mapped_column(Text)

    session_id: Mapped[str | None] = mapped_column(
        String(100), 
        nullable=True
    )

    resume_text: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    checkpoint_version: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=1
    )

    match_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    final_report: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc8,
        onupdate=now_utc8,
    )
