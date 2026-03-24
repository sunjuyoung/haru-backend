"""
Agent 5 — Memory Rewriter (존재하지 않은 기억)
- 후회/아쉬움이 담긴 일기 → "만약 다르게 행동했다면?" 가상의 리메이크 이야기 생성
- 이야기 + 몽환적 수채화 스타일 이미지 생성
- CrewAI + GPT-4o + Replicate FLUX.1
"""

import json
import uuid

from crewai import Agent, Crew, Task

from app.core.config import settings
from app.core.storage import upload_image_from_url
from app.agents.art_agent import _call_replicate
from app.schemas.ai import EmotionAnalysis

_MODEL = "gpt-4o-mini" if settings.DEBUG else "gpt-4o"


class MemoryResult:
    """Memory Rewriter 결과 — 텍스트 + 이미지"""
    def __init__(self, rewritten_scene: str, memory_image_url: str | None = None):
        self.rewritten_scene = rewritten_scene
        self.memory_image_url = memory_image_url

    def model_dump(self) -> dict:
        return {
            "rewritten_scene": self.rewritten_scene,
            "memory_image_url": self.memory_image_url,
        }


# === 몽환적 수채화 이미지 생성 ===

def _generate_memory_image_prompt(rewritten_scene: str, emotion: EmotionAnalysis) -> str:
    """CrewAI로 "존재하지 않은 기억" 텍스트 → 몽환적 수채화 이미지 프롬프트 생성"""
    agent = Agent(
        role="기억의 화가",
        goal="가상의 기억 이야기를 몽환적이고 따뜻한 수채화 이미지로 표현하기 위한 영어 프롬프트를 만든다",
        backstory=(
            "당신은 존재하지 않았던 기억을 아름다운 그림으로 그리는 화가입니다. "
            "가정법으로 쓰인 따뜻한 이야기를 읽고, 몽환적이고 부드러운 수채화 스타일의 "
            "이미지로 변환합니다. 현실과 꿈의 경계에 있는 듯한 느낌을 강조합니다."
        ),
        llm=_MODEL,
        verbose=settings.DEBUG,
    )

    task = Task(
        description=f"""다음 "존재하지 않은 기억" 이야기를 바탕으로 이미지 생성 프롬프트를 만들어주세요.

[가상의 기억]
{rewritten_scene}

[감정 분석]
- 주요 감정: {emotion.primary_emotion}
- 분위기: {emotion.mood}
- 감정 색상: {emotion.emotion_color}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "prompt": "영어 이미지 생성 프롬프트 (100단어 이내)"
}}

프롬프트 작성 규칙:
- 반드시 영어로 작성
- "dreamy watercolor", "soft ethereal glow", "pastel tones", "blurred edges", "misty atmosphere" 등 몽환적 수채화 키워드 포함
- 이야기에서 핵심 장면이나 오브젝트를 추출하여 묘사
- 사람의 얼굴은 가급적 피하고, 풍경/사물/분위기 중심
- 현실과 꿈의 경계에 있는 듯한 따뜻한 느낌
- 기존 연필 스케치와 확실히 다른 수채화 스타일""",
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


def _create_memory_image(rewritten_scene: str, emotion: EmotionAnalysis) -> str:
    """
    "존재하지 않은 기억" 텍스트 → 몽환적 수채화 이미지 생성
    1. Replicate rate limit 회피를 위해 10초 대기 (메인 스케치 이후 간격 확보)
    2. CrewAI로 프롬프트 생성
    3. Replicate FLUX.1로 이미지 생성
    4. R2/로컬에 업로드
    """
    import time
    time.sleep(10)

    prompt = _generate_memory_image_prompt(rewritten_scene, emotion)
    temp_url = _call_replicate(prompt)
    filename = f"memories/{uuid.uuid4()}.webp"
    permanent_url = upload_image_from_url(temp_url, filename)
    return permanent_url


# === 텍스트 생성 ===

def rewrite_memory(diary_content: str, emotion: EmotionAnalysis) -> MemoryResult:
    """
    일기 + 감정 분석 → "존재하지 않은 기억" 생성 (동기 함수)

    1단계: 후회/아쉬움이 담긴 일기 → 따뜻한 가상의 이야기 생성
    2단계: 가상의 이야기 → 몽환적 수채화 이미지 생성
    """
    # 1단계: 텍스트 생성
    agent = Agent(
        role="기억 리라이터",
        goal="후회가 담긴 일기를 읽고, '만약 다르게 행동했다면' 어땠을지 따뜻한 가상의 이야기를 쓴다",
        backstory=(
            "당신은 사람들의 후회를 따뜻한 가능성으로 바꿔주는 이야기꾼입니다. "
            "일기에서 후회나 아쉬움을 읽어내고, '만약 그때 다르게 했다면' 어떤 "
            "이야기가 펼쳐졌을지 상상합니다. 비현실적인 판타지가 아니라, "
            "충분히 가능했을 법한 따뜻한 대안을 제시합니다."
        ),
        llm=_MODEL,
        verbose=settings.DEBUG,
    )

    task = Task(
        description=f"""다음 일기에는 후회나 아쉬움이 담겨 있습니다.
"만약 그때 다르게 행동했다면?" 어땠을지 가상의 이야기를 써주세요.

[일기 내용]
{diary_content}

[감정 분석]
- 주요 감정: {emotion.primary_emotion}
- 키워드: {', '.join(emotion.emotion_keywords)}
- 후회 신뢰도: {emotion.regret_confidence}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "rewritten_scene": "3~5문장의 가상의 리메이크 이야기"
}}

작성 규칙:
- 한국어로 작성
- 원래 일기의 상황을 존중하되, 다른 선택을 했을 때의 장면을 묘사
- 따뜻하고 희망적인 톤 유지
- "~했을지도 모른다", "~했을 것이다" 같은 가정법 사용
- 3~5문장으로 간결하게""",
        expected_output="가상의 리메이크 이야기 JSON",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=settings.DEBUG)
    result = crew.kickoff()

    raw = str(result)
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]

    parsed = json.loads(raw.strip())
    rewritten_scene = parsed["rewritten_scene"]

    # 2단계: 몽환적 수채화 이미지 생성 (실패해도 텍스트는 살림)
    memory_image_url = None
    try:
        memory_image_url = _create_memory_image(rewritten_scene, emotion)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Memory image generation failed (text preserved): {e}")

    return MemoryResult(
        rewritten_scene=rewritten_scene,
        memory_image_url=memory_image_url,
    )
