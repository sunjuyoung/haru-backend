"""
Mock 에이전트 — 외부 API 없이 파이프라인 테스트용
- DEBUG 모드에서 실제 CrewAI/Replicate/R2 호출 대신 사용
- 고정된 더미 데이터를 0.5~1초 지연 후 반환
"""

import random
import time

from app.schemas.ai import ArtResult, EmotionAnalysis, PoetResult

# 다양한 Mock 감정 데이터 풀
_MOCK_EMOTIONS = [
    EmotionAnalysis(
        primary_emotion="감사",
        emotion_keywords=["따뜻함", "감사", "행복"],
        mood="따뜻한",
        emotion_color="#FFB347",
        regret_confidence=0.1,
    ),
    EmotionAnalysis(
        primary_emotion="그리움",
        emotion_keywords=["그리움", "추억", "쓸쓸함"],
        mood="쓸쓸한",
        emotion_color="#7B9EC7",
        regret_confidence=0.3,
    ),
    EmotionAnalysis(
        primary_emotion="후회",
        emotion_keywords=["후회", "아쉬움", "반성"],
        mood="무거운",
        emotion_color="#8B7D6B",
        regret_confidence=0.85,
    ),
]

_MOCK_POEMS = [
    PoetResult(
        poetic_title="오늘도 괜찮은 하루",
        poem_text="햇살이 창문을 두드리던 오후\n커피 한 잔의 온기가\n마음까지 데워주던\n그런 하루였다",
    ),
    PoetResult(
        poetic_title="빗소리에 잠기다",
        poem_text="유리창을 타고 흐르는 빗줄기\n그 안에 비친 내 얼굴이\n오늘따라 낯설어서\n한참을 들여다보았다",
    ),
    PoetResult(
        poetic_title="다시 걷는 길",
        poem_text="돌아갈 수 없는 길이라 해도\n발자국은 남아 있으니\n다음에는 조금 더\n천천히 걸어보려 한다",
    ),
]


def mock_analyze_emotion(diary_content: str) -> EmotionAnalysis:
    """Mock 감정 분석 — 일기 내용에 '후회/아쉬움' 포함 시 후회 감정 반환"""
    time.sleep(random.uniform(0.3, 0.8))

    # 후회 관련 키워드가 있으면 후회 감정 반환
    regret_words = ["후회", "아쉬움", "미안", "그때", "잘못", "반성"]
    if any(word in diary_content for word in regret_words):
        return _MOCK_EMOTIONS[2]  # 후회

    return random.choice(_MOCK_EMOTIONS[:2])


def mock_write_poem(diary_content: str, emotion: EmotionAnalysis) -> PoetResult:
    """Mock 시 생성"""
    time.sleep(random.uniform(0.3, 0.8))
    return random.choice(_MOCK_POEMS)


def mock_create_sketch(diary_content: str, emotion: EmotionAnalysis) -> ArtResult:
    """Mock 스케치 생성 — placeholder 이미지 URL 반환"""
    time.sleep(random.uniform(0.5, 1.0))
    return ArtResult(
        sketch_prompt="A warm pencil sketch of a quiet afternoon scene (mock)",
        sketch_image_url="https://placehold.co/512x512/f5f0eb/8b7d6b?text=Sketch+Mock",
    )


def mock_rewrite_memory(diary_content: str, emotion: EmotionAnalysis):
    """Mock 기억 리라이터 — "존재하지 않은 기억" 더미 데이터"""
    from app.agents.memory_agent import MemoryResult
    time.sleep(random.uniform(0.3, 0.8))
    return MemoryResult(
        rewritten_scene=(
            "그때 용기를 내어 한마디 더 건넸다면, "
            "아마 우리는 카페 창가에서 해가 질 때까지 이야기를 나눴을 것이다. "
            "돌아가는 길에 조금은 더 가벼운 마음으로 걸었을지도 모른다."
        ),
    )
