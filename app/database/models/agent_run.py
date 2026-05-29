from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base
from app.utils.time import now_utc8


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    user_id: Mapped[str] = mapped_column(String(255), index=True)

    status: Mapped[str] = mapped_column(String(50), index=True)

    jd_text: Mapped[str] = mapped_column(Text)

    final_report: Mapped[str] = mapped_column(Text)

    error_message: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc8
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc8, onupdate=now_utc8
    )
