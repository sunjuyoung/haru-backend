"""
"존재하지 않은 기억" 모델
- 후회/반성이 감지된 일기에 대해 AI가 생성한 가상의 리메이크 이야기
- Sprint 4에서 본격 사용
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    diary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diaries.id"), nullable=False
    )
    rewritten_scene: Mapped[str] = mapped_column(Text, nullable=False)
    memory_image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)  # soft delete

    # === 관계 ===
    diary: Mapped["Diary"] = relationship(back_populates="memory")


from app.models.diary import Diary  # noqa: E402, F401
