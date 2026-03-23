"""
에이전트 비동기 실행기 (v2.3 패턴)
- ThreadPoolExecutor로 CrewAI 동기 코드를 스레드 분리
- asyncio.wait_for로 타임아웃 제어
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable

from app.core.config import settings

# 글로벌 스레드 풀 — 앱 전체에서 단일 인스턴스 사용
executor = ThreadPoolExecutor(max_workers=settings.AGENT_MAX_WORKERS)


async def run_agent_with_timeout(
    func: Callable[..., Any],
    *args: Any,
    timeout: int | None = None,
) -> Any:
    """
    동기 에이전트 함수를 비동기로 실행 + 타임아웃 적용

    Args:
        func: 실행할 동기 함수 (예: crew.kickoff)
        *args: 함수에 전달할 인자
        timeout: 타임아웃(초). None이면 설정값 사용

    Returns:
        함수 실행 결과

    Raises:
        asyncio.TimeoutError: 타임아웃 초과 시
    """
    if timeout is None:
        timeout = settings.AGENT_TIMEOUT_SECONDS

    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(executor, partial(func, *args)),
        timeout=timeout,
    )
