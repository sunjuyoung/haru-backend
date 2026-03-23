"""
AI 파이프라인 결과 스키마
- EmotionAnalysis: 감정 분석 결과 (Agent 1)
- PoetResult: 시적 제목 + 시 본문 (Agent 2)
- ArtResult: 스케치 이미지 정보 (Agent 3)
- GenerationResult: 전체 파이프라인 통합 결과
"""

from pydantic import BaseModel, Field


class EmotionAnalysis(BaseModel):
    """감정 분석 결과 — v2.3 순수 데이터 모델 (has_regret 없음)"""
    primary_emotion: str = Field(description="주요 감정 (예: 기쁨, 슬픔, 불안)")
    emotion_keywords: list[str] = Field(description="감정 키워드 목록")
    mood: str = Field(description="전체적인 분위기 (예: 따뜻한, 차분한, 쓸쓸한)")
    emotion_color: str = Field(description="감정을 표현하는 HEX 컬러 (#RRGGBB)")
    regret_confidence: float = Field(
        ge=0.0, le=1.0,
        description="후회/반성/아쉬움 감지 신뢰도 (0.0~1.0)",
    )


class PoetResult(BaseModel):
    """시인 에이전트 결과 — 시적 제목 + 시 본문"""
    poetic_title: str = Field(description="일기에 어울리는 시적 제목")
    poem_text: str = Field(description="일기 내용을 바탕으로 쓴 짧은 시")


class ArtResult(BaseModel):
    """아트 디렉터 에이전트 결과 — 스케치 이미지 URL"""
    sketch_prompt: str = Field(description="이미지 생성에 사용된 프롬프트")
    sketch_image_url: str = Field(description="R2에 업로드된 스케치 이미지 URL")


class GenerationResult(BaseModel):
    """전체 AI 파이프라인 통합 결과"""
    emotion: EmotionAnalysis
    poet: PoetResult
    art: ArtResult
    sound_key: str | None = Field(default=None, description="ASMR 사운드 매핑 키 (Sprint 5)")
