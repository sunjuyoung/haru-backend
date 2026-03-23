"""
Agent 3 — 아트 디렉터 에이전트
- 감정 분석 + 일기 내용 → 영어 스케치 프롬프트 생성 (CrewAI)
- 프롬프트 → Replicate FLUX.1 호출 → 이미지 URL 반환
- 이미지를 R2에 업로드하여 영구 URL 생성
"""

import json
import uuid

import replicate
from crewai import Agent, Crew, Task

from app.core.config import settings
from app.core.storage import upload_image_from_url
from app.schemas.ai import ArtResult, EmotionAnalysis

_MODEL = "gpt-4o-mini" if settings.DEBUG else "gpt-4o"

# Replicate FLUX.1 모델 — 연필 스케치 스타일
_FLUX_MODEL = "black-forest-labs/flux-1.1-pro"


def _generate_sketch_prompt(diary_content: str, emotion: EmotionAnalysis) -> str:
    """CrewAI로 일기 + 감정 분석 → 영어 스케치 프롬프트 생성"""
    agent = Agent(
        role="아트 디렉터",
        goal="일기의 감정을 연필 스케치 이미지로 표현하기 위한 영어 프롬프트를 만든다",
        backstory=(
            "당신은 감정을 시각적 이미지로 변환하는 아트 디렉터입니다. "
            "일기의 감정과 분위기를 따뜻한 연필 스케치 스타일의 이미지로 표현합니다. "
            "프롬프트는 반드시 영어로 작성하며, 연필 스케치 특유의 부드러운 질감을 강조합니다."
        ),
        llm=_MODEL,
        verbose=settings.DEBUG,
    )

    task = Task(
        description=f"""다음 일기와 감정 분석을 바탕으로 이미지 생성 프롬프트를 만들어주세요.

[일기 내용]
{diary_content}

[감정 분석]
- 주요 감정: {emotion.primary_emotion}
- 키워드: {', '.join(emotion.emotion_keywords)}
- 분위기: {emotion.mood}
- 감정 색상: {emotion.emotion_color}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "prompt": "영어 이미지 생성 프롬프트 (100단어 이내)"
}}

프롬프트 작성 규칙:
- 반드시 영어로 작성
- "pencil sketch", "hand-drawn", "warm", "soft lines" 등 연필 스케치 스타일 키워드 포함
- 일기에서 핵심 장면이나 오브젝트를 추출하여 묘사
- 사람의 얼굴은 가급적 피하고, 풍경/사물/분위기 중심
- 색상은 단색(흑연) 또는 부드러운 톤""",
        expected_output="이미지 생성 프롬프트 JSON",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=settings.DEBUG)
    result = crew.kickoff()

    raw = str(result)
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]

    parsed = json.loads(raw.strip())
    return parsed["prompt"]


def _call_replicate(prompt: str) -> str:
    """Replicate FLUX.1 호출 → 생성된 이미지 URL 반환"""
    output = replicate.run(
        _FLUX_MODEL,
        input={
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "webp",
            "output_quality": 80,
            "safety_tolerance": 2,
        },
    )
    # Replicate 반환 타입: str, FileOutput, 또는 리스트
    # FileOutput은 .url 속성을 가지거나 str()로 변환 가능
    if isinstance(output, str):
        return output
    if hasattr(output, "url"):
        return str(output.url)
    # 이터러블(리스트)인 경우 첫 번째 항목
    try:
        items = list(output)
        if items:
            item = items[0]
            return str(item.url) if hasattr(item, "url") else str(item)
    except TypeError:
        pass
    return str(output)


def create_sketch(diary_content: str, emotion: EmotionAnalysis) -> ArtResult:
    """
    일기 + 감정 분석 → 스케치 이미지 생성 (동기 함수)
    1. CrewAI로 프롬프트 생성
    2. Replicate로 이미지 생성
    3. R2에 업로드
    """
    # 1단계: 스케치 프롬프트 생성
    prompt = _generate_sketch_prompt(diary_content, emotion)

    # 2단계: Replicate에서 이미지 생성
    temp_url = _call_replicate(prompt)

    # 3단계: R2에 업로드하여 영구 URL 생성
    filename = f"sketches/{uuid.uuid4()}.webp"
    permanent_url = upload_image_from_url(temp_url, filename)

    return ArtResult(
        sketch_prompt=prompt,
        sketch_image_url=permanent_url,
    )
