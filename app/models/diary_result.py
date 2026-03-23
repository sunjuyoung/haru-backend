"""
AI 생성 결과 모델
- 감정 분석 + 시적 제목/시 + 스케치 이미지 URL
- soft delete 지원 (deleted_at)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DiaryResult(Base):
    __tablename__ = "diary_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    diary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diaries.id"), nullable=False
    )

    # === 감정 분석 결과 (Agent 1) ===
    primary_emotion: Mapped[str] = mapped_column(String(50), nullable=False)
    emotion_keywords: Mapped[list] = mapped_column(JSONB, nullable=False)
    mood: Mapped[str] = mapped_column(String(50), nullable=False)
    emotion_color: Mapped[str] = mapped_column(String(7), nullable=False)  # HEX (#RRGGBB)
    regret_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # === 시 생성 결과 (Agent 2) ===
    poetic_title: Mapped[str] = mapped_column(String(200), nullable=False)
    poem_text: Mapped[str] = mapped_column(Text, nullable=False)

    # === 스케치 이미지 (Agent 3) ===
    sketch_image_url: Mapped[str] = mapped_column(Text, nullable=False)

    # === 사운드 매핑 (Sprint 5) ===
    sound_key: Mapped[str | None] = mapped_column(String(100))

    # === 타임스탬프 ===
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)  # soft delete

    # === 관계 ===
    diary: Mapped["Diary"] = relationship(back_populates="result")


from app.models.diary import Diary  # noqa: E402, F401
