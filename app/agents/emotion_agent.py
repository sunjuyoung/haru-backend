"""
Agent 1 — 감정 분석 에이전트
- 일기 텍스트를 입력받아 감정 분석 결과를 JSON으로 반환
- CrewAI + GPT-4o (개발 중 gpt-4o-mini 사용 가능)
"""

import json

from crewai import Agent, Crew, Task

from app.core.config import settings
from app.schemas.ai import EmotionAnalysis

# GPT 모델 설정 — 개발 비용 절감을 위해 mini 옵션 제공
_MODEL = "gpt-4o-mini" if settings.DEBUG else "gpt-4o"


def analyze_emotion(diary_content: str) -> EmotionAnalysis:
    """
    일기 텍스트 → 감정 분석 결과 (동기 함수)

    CrewAI Crew.kickoff()은 동기 실행이므로
    run_agent_with_timeout()으로 감싸서 호출해야 합니다.
    """
    agent = Agent(
        role="감정 분석 전문가",
        goal="일기 텍스트에서 작성자의 감정을 정확하게 분석한다",
        backstory=(
            "당신은 심리 상담과 감정 분석 분야의 전문가입니다. "
            "사람들이 쓴 일기를 읽고 그 안에 담긴 감정의 결을 섬세하게 읽어냅니다. "
            "후회나 아쉬움이 담긴 표현도 놓치지 않습니다."
        ),
        llm=_MODEL,
        verbose=settings.DEBUG,
    )

    task = Task(
        description=f"""다음 일기를 읽고 감정을 분석해주세요.

---
{diary_content}
---

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{
    "primary_emotion": "주요 감정 (한국어, 예: 기쁨, 슬픔, 불안, 감사, 외로움 등)",
    "emotion_keywords": ["감정 키워드1", "감정 키워드2", "감정 키워드3"],
    "mood": "전체적인 분위기 (한국어, 예: 따뜻한, 차분한, 쓸쓸한, 설레는 등)",
    "emotion_color": "#RRGGBB 형식의 감정 색상 코드",
    "regret_confidence": 0.0~1.0 사이의 후회/반성/아쉬움 감지 신뢰도
}}

주의사항:
- primary_emotion은 한국어로 한 단어
- emotion_keywords는 3~5개
- emotion_color는 감정을 시각적으로 표현하는 색상
- regret_confidence: 후회/반성/아쉬움 표현이 강하면 0.7 이상, 없으면 0.1 이하""",
        expected_output="감정 분석 결과 JSON",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=settings.DEBUG)
    result = crew.kickoff()

    # CrewAI 결과에서 JSON 파싱
    raw = str(result)
    # JSON 블록 추출 (```json ... ``` 형태 대응)
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]

    parsed = json.loads(raw.strip())
    return EmotionAnalysis(**parsed)
