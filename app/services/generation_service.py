"""
AI 생성 서비스 (v2.3 완전 통합)
- SSE 스트리밍 기반 파이프라인 오케스트레이션
- 3단계 exception 격리: 핵심(poet+art) 실패→에러, 부가(memory) 실패→None
- 덮어쓰기 흐름: soft delete → 파이프라인 → 성공 시 이미지 삭제 / 실패 시 rollback
- 단계별 SSE 이벤트 발행
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import analyze_emotion, create_sketch, rewrite_memory, write_poem
from app.agents.executor import run_agent_with_timeout
from app.core.storage import delete_image
from app.models.diary import Diary
from app.models.diary_result import DiaryResult
from app.models.memory import Memory
from app.schemas.ai import EmotionAnalysis
from app.services.sound import match_sound
from app.utils.sse import sse_event

logger = logging.getLogger(__name__)

# "존재하지 않은 기억" 생성 임계값 (v2.3)
# TODO: 사운드 에셋 추가 후 0.6으로 복원
REGRET_THRESHOLD = 0.3


def should_generate_memory(emotion: EmotionAnalysis) -> bool:
    """후회/반성/아쉬움 감지 여부 판별 (v2.3)"""
    return emotion.regret_confidence >= REGRET_THRESHOLD


# === 덮어쓰기 관련 함수 (v2.3 섹션 5~6) ===

def collect_urls_for_deletion(diary: Diary) -> list[str]:
    """기존 결과에서 삭제 대상 이미지 URL 수집 (삭제는 아직 안 함)"""
    urls: list[str] = []
    if diary.result and diary.result.deleted_at is None:
        if diary.result.sketch_image_url:
            urls.append(diary.result.sketch_image_url)
    if diary.memory and diary.memory.deleted_at is None:
        if diary.memory.memory_image_url:
            urls.append(diary.memory.memory_image_url)
    return urls


async def soft_delete_existing_results(db: AsyncSession, diary: Diary) -> None:
    """기존 결과를 soft delete (deleted_at 설정)"""
    now = datetime.utcnow()
    if diary.result and diary.result.deleted_at is None:
        diary.result.deleted_at = now
    if diary.memory and diary.memory.deleted_at is None:
        diary.memory.deleted_at = now
    await db.flush()


async def rollback_soft_delete(db: AsyncSession, diary: Diary) -> None:
    """soft delete 롤백 (파이프라인 실패 시)"""
    if diary.result and diary.result.deleted_at is not None:
        diary.result.deleted_at = None
    if diary.memory and diary.memory.deleted_at is not None:
        diary.memory.deleted_at = None
    await db.flush()


def delete_images_fire_and_forget(urls: list[str]) -> None:
    """이미지 비동기 삭제 (fire-and-forget, 실패해도 무시)"""
    for url in urls:
        try:
            # URL에서 파일명 추출 (uploads/sketches/xxx.webp 또는 R2 경로)
            if "/uploads/" in url:
                filename = url.split("/uploads/")[-1]
            elif "/" in url:
                filename = "/".join(url.split("/")[-2:])
            else:
                continue
            delete_image(filename)
            logger.info(f"Deleted image: {filename}")
        except Exception as e:
            logger.warning(f"Failed to delete image {url}: {e}")


# === Memory Agent safe wrapper ===

async def run_memory_agent_safe(content: str, emotion: EmotionAnalysis):
    """
    Memory Rewriter safe wrapper — 파싱/타임아웃 실패 시 None 반환
    부가 에이전트이므로 실패해도 전체 파이프라인에 영향 없음
    """
    try:
        # 텍스트 생성 + 10초 대기(Replicate rate limit) + 이미지 생성 고려하여 timeout 180초
        result = await run_agent_with_timeout(rewrite_memory, content, emotion, timeout=180)
        return result
    except asyncio.TimeoutError:
        logger.warning("Agent 5 (Memory Rewriter) timed out")
        return None
    except Exception as e:
        logger.warning(f"Agent 5 (Memory Rewriter) failed: {e}")
        return None


# === 결과 저장 ===

async def save_generation_results(
    db: AsyncSession,
    diary: Diary,
    emotion: EmotionAnalysis,
    poet_result,
    art_result,
    memory_result=None,
) -> DiaryResult:
    """
    생성 결과를 단일 트랜잭션으로 atomic 저장 (v2.3 섹션 4)
    diary_result + memory를 하나의 트랜잭션에서 저장
    사운드 매칭도 여기서 자동 수행
    """
    # 감정 기반 사운드 매칭
    sound_key = match_sound(emotion.primary_emotion)

    async with db.begin_nested():
        diary_result = DiaryResult(
            diary_id=diary.id,
            primary_emotion=emotion.primary_emotion,
            emotion_keywords=emotion.emotion_keywords,
            mood=emotion.mood,
            emotion_color=emotion.emotion_color,
            regret_confidence=emotion.regret_confidence,
            poetic_title=poet_result.poetic_title,
            poem_text=poet_result.poem_text,
            sketch_image_url=art_result.sketch_image_url,
            sound_key=sound_key,
        )
        db.add(diary_result)

        if memory_result is not None:
            memory = Memory(
                diary_id=diary.id,
                rewritten_scene=memory_result.rewritten_scene,
                memory_image_url=memory_result.memory_image_url,
            )
            db.add(memory)

    await db.commit()
    await db.refresh(diary_result)
    return diary_result


# === SSE 스트리밍 파이프라인 ===

async def diary_generation_stream(
    db: AsyncSession,
    diary: Diary,
) -> AsyncGenerator[str, None]:
    """
    SSE 스트리밍 파이프라인 — v2.3 완전 통합

    이벤트 흐름:
    1. started
    2. step:analyzing → 감정 분석
    3. step:analyzed → 감정 결과
    4. step:creating → 시 + 스케치 (+ 조건부 memory) 병렬 생성
    5. step:drawing → 시 완료, 스케치 진행 중
    6. step:imagining → "존재하지 않은 기억" 생성 중 (조건부)
    7. step:finishing → DB 저장
    8. complete / error
    """
    content = diary.content
    is_overwrite = diary.result is not None and diary.result.deleted_at is None
    old_urls: list[str] = []

    try:
        # === 덮어쓰기 준비 ===
        if is_overwrite:
            old_urls = collect_urls_for_deletion(diary)
            await soft_delete_existing_results(db, diary)

        # === started ===
        yield sse_event("started", {
            "diary_id": str(diary.id),
            "is_overwrite": is_overwrite,
        })

        # === Phase A: 감정 분석 ===
        yield sse_event("step", {"phase": "analyzing", "message": "오늘의 이야기를 읽고 있어요..."})

        emotion = await run_agent_with_timeout(analyze_emotion, content, timeout=60)

        yield sse_event("step", {
            "phase": "analyzed",
            "message": f"'{emotion.primary_emotion}'의 감정을 느꼈어요",
            "emotion": emotion.model_dump(),
        })

        # === Phase B: 3단계 exception 격리 병렬 실행 (v2.3 섹션 2) ===
        yield sse_event("step", {"phase": "creating", "message": "어떤 하루였는지 느끼며 그리는 중..."})

        # [Step 1] 모든 에이전트를 Task로 생성 (즉시 시작)
        poet_task = asyncio.create_task(
            run_agent_with_timeout(write_poem, content, emotion, timeout=60)
        )
        art_task = asyncio.create_task(
            run_agent_with_timeout(create_sketch, content, emotion, timeout=120)
        )

        # 조건부: memory agent (부가 에이전트)
        generate_memory = should_generate_memory(emotion)
        memory_task = None
        if generate_memory:
            memory_task = asyncio.create_task(run_memory_agent_safe(content, emotion))

        # [Step 2] 핵심 에이전트 대기 — 실패 시 예외 전파
        poet_result = await poet_task

        yield sse_event("step", {
            "phase": "drawing",
            "message": "스케치를 마무리하는 중...",
            "poet": poet_result.model_dump(),
        })

        art_result = await art_task

        # [Step 3] 부가 에이전트 대기 — 실패 시 격리 (graceful degradation)
        memory_result = None
        if memory_task:
            yield sse_event("step", {"phase": "imagining", "message": "다른 가능성을 상상하는 중..."})
            memory_result = await memory_task

        # === Phase C: DB 저장 ===
        yield sse_event("step", {"phase": "finishing", "message": "어울리는 소리를 입히는 중..."})

        diary_result = await save_generation_results(
            db=db,
            diary=diary,
            emotion=emotion,
            poet_result=poet_result,
            art_result=art_result,
            memory_result=memory_result,
        )

        # 덮어쓰기 성공 → 이전 이미지 삭제 (fire-and-forget)
        if old_urls:
            delete_images_fire_and_forget(old_urls)

        # === complete ===
        yield sse_event("complete", {
            "diary_id": str(diary.id),
            "result_id": str(diary_result.id),
            "emotion": emotion.model_dump(),
            "poet": poet_result.model_dump(),
            "art": art_result.model_dump(),
            "memory": memory_result.model_dump() if memory_result else None,
            "has_memory": memory_result is not None,
            "sound_key": diary_result.sound_key,
        })

    except asyncio.TimeoutError:
        # 덮어쓰기 실패 → soft delete 롤백
        if is_overwrite:
            await rollback_soft_delete(db, diary)
            await db.commit()

        yield sse_event("error", {
            "message": "AI 생성 시간이 초과되었어요. 잠시 후 다시 시도해주세요.",
            "code": "TIMEOUT",
        })

    except Exception as e:
        logger.error(f"Generation pipeline failed: {e}")

        # 덮어쓰기 실패 → soft delete 롤백
        if is_overwrite:
            await rollback_soft_delete(db, diary)
            await db.commit()

        yield sse_event("error", {
            "message": "생성 중 문제가 발생했어요. 다시 시도해주세요.",
            "code": "INTERNAL_ERROR",
            "detail": str(e),
        })
