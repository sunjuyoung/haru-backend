"""
에이전트 모듈 — DEBUG 모드에 따라 실제/Mock 에이전트 자동 선택

사용법:
    from app.agents import analyze_emotion, write_poem, create_sketch, rewrite_memory
"""

from app.core.config import settings

if settings.DEBUG and not settings.OPENAI_API_KEY:
    # API 키가 없는 DEBUG 모드 → Mock 에이전트 사용
    from app.agents.mock_agents import (
        mock_analyze_emotion as analyze_emotion,
        mock_create_sketch as create_sketch,
        mock_rewrite_memory as rewrite_memory,
        mock_write_poem as write_poem,
    )
else:
    # 실제 에이전트 사용
    from app.agents.emotion_agent import analyze_emotion  # noqa: F401
    from app.agents.poet_agent import write_poem  # noqa: F401
    from app.agents.art_agent import create_sketch  # noqa: F401
    from app.agents.memory_agent import rewrite_memory  # noqa: F401
