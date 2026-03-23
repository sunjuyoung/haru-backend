"""
Agent 5 — Memory Rewriter (존재하지 않은 기억)
- 후회/아쉬움이 담긴 일기 → "만약 다르게 행동했다면?" 가상의 리메이크 이야기 생성
- CrewAI + GPT-4o
"""

import json

from crewai import Agent, Crew, Task

from app.core.config import settings
from app.schemas.ai import EmotionAnalysis

_MODEL = "gpt-4o-mini" if settings.DEBUG else "gpt-4o"


class MemoryResult:
    """Memory Rewriter 결과"""
    def __init__(self, rewritten_scene: str):
        self.rewritten_scene = rewritten_scene

    def model_dump(self) -> dict:
        return {"rewritten_scene": self.rewritten_scene}


def rewrite_memory(diary_content: str, emotion: EmotionAnalysis) -> MemoryResult:
    """
    일기 + 감정 분석 → "존재하지 않은 기억" 생성 (동기 함수)

    후회/아쉬움이 담긴 일기를 읽고, "만약 그때 다르게 행동했다면?"이라는
    따뜻하고 희망적인 가상의 이야기를 만들어냅니다.
    """
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
    return MemoryResult(rewritten_scene=parsed["rewritten_scene"])
