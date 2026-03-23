"""
Agent 2 — 시인 에이전트
- 감정 분석 결과 + 일기 내용을 바탕으로 시적 제목과 짧은 시를 생성
- CrewAI + GPT-4o
"""

import json

from crewai import Agent, Crew, Task

from app.core.config import settings
from app.schemas.ai import EmotionAnalysis, PoetResult

_MODEL = "gpt-4o-mini" if settings.DEBUG else "gpt-4o"


def write_poem(diary_content: str, emotion: EmotionAnalysis) -> PoetResult:
    """
    일기 + 감정 분석 → 시적 제목 + 시 본문 (동기 함수)
    """
    agent = Agent(
        role="시인",
        goal="일기의 감정을 담은 아름다운 시적 제목과 짧은 시를 쓴다",
        backstory=(
            "당신은 사람들의 일상에서 시를 발견하는 시인입니다. "
            "일기를 읽고 그 안의 감정을 따뜻하고 서정적인 한국어 시로 표현합니다. "
            "제목은 짧지만 여운이 남는 문장으로, 시는 4~6줄의 자유시로 씁니다."
        ),
        llm=_MODEL,
        verbose=settings.DEBUG,
    )

    task = Task(
        description=f"""다음 일기와 감정 분석 결과를 바탕으로 시적 제목과 짧은 시를 써주세요.

[일기 내용]
{diary_content}

[감정 분석]
- 주요 감정: {emotion.primary_emotion}
- 키워드: {', '.join(emotion.emotion_keywords)}
- 분위기: {emotion.mood}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "poetic_title": "시적인 제목 (15자 이내)",
    "poem_text": "4~6줄의 짧은 자유시"
}}

주의사항:
- 한국어로 작성
- 제목은 일기의 핵심 감정을 시적으로 압축
- 시는 줄바꿈(\\n)으로 구분된 4~6줄
- 과도한 미사여구 없이 담백하게""",
        expected_output="시적 제목과 시 본문 JSON",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=settings.DEBUG)
    result = crew.kickoff()

    raw = str(result)
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]

    parsed = json.loads(raw.strip())
    return PoetResult(**parsed)
