"""
일기 API 요청/응답 스키마
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# === 요청 ===

class DiaryCreate(BaseModel):
    """일기 생성 요청"""
    content: str = Field(min_length=1, max_length=5000, description="일기 내용")
    written_date: date = Field(description="일기 날짜 (YYYY-MM-DD)")


# === 응답 ===

class DiaryResultResponse(BaseModel):
    """AI 생성 결과 응답"""
    id: uuid.UUID
    primary_emotion: str
    emotion_keywords: list[str]
    mood: str
    emotion_color: str
    regret_confidence: float
    poetic_title: str
    poem_text: str
    sketch_image_url: str
    sound_key: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiaryResponse(BaseModel):
    """일기 단일 응답"""
    id: uuid.UUID
    content: str
    written_date: date
    is_overwrite: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryResponse(BaseModel):
    """'존재하지 않은 기억' 응답"""
    id: uuid.UUID
    rewritten_scene: str
    memory_image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiaryDetailResponse(BaseModel):
    """일기 상세 응답 (AI 결과 + 기억 포함)"""
    id: uuid.UUID
    content: str
    written_date: date
    is_overwrite: bool
    result: DiaryResultResponse | None = None
    memory: MemoryResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiaryListItem(BaseModel):
    """일기 목록 항목 (내용 미포함, 미리보기만)"""
    id: uuid.UUID
    written_date: date
    content_preview: str = Field(description="일기 내용 앞 50자")
    poetic_title: str | None = Field(default=None, description="시적 제목 (AI 생성 결과)")
    has_result: bool = Field(description="AI 생성 결과 존재 여부")
    created_at: datetime


class DiaryListResponse(BaseModel):
    """일기 목록 응답 (월별)"""
    year: int
    month: int
    diaries: list[DiaryListItem]
    total: int


# === 책장 갤러리 ===

class BookshelfMonth(BaseModel):
    """책장 갤러리 — 월별 책 한 권"""
    month: int = Field(ge=1, le=12, description="월 (1~12)")
    diary_count: int = Field(description="해당 월 일기 수")
    has_result: bool = Field(description="AI 생성 결과가 있는 일기 존재 여부")
    cover_image_url: str | None = Field(default=None, description="대표 스케치 이미지 URL")
    cover_emotion_color: str | None = Field(default=None, description="대표 감정 색상 (#RRGGBB)")
    cover_title: str | None = Field(default=None, description="대표 시적 제목")


class BookshelfResponse(BaseModel):
    """책장 갤러리 응답 (연간 12개월)"""
    year: int
    months: list[BookshelfMonth] = Field(description="12개월 책장 데이터")
