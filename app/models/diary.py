"""
일기 모델
- 사용자가 작성한 일기 원문 저장
- written_date: 일기 날짜 (작성일 != 기록일 가능)
- user_id + written_date UNIQUE 제약 → 날짜당 1개 일기
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Diary(Base):
    __tablename__ = "diaries"
    __table_args__ = (
        UniqueConstraint("user_id", "written_date", name="uq_user_written_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    written_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_overwrite: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=datetime.now
    )

    # === 관계 ===
    user: Mapped["User"] = relationship(back_populates="diaries")
    result: Mapped["DiaryResult | None"] = relationship(back_populates="diary", uselist=False)
    memory: Mapped["Memory | None"] = relationship(back_populates="diary", uselist=False)


from app.models.user import User  # noqa: E402, F401
from app.models.diary_result import DiaryResult  # noqa: E402, F401
from app.models.memory import Memory  # noqa: E402, F401
