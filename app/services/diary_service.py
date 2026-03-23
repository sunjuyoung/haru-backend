"""
일기 비즈니스 로직
- 일기 생성 (날짜 중복 체크)
- 월별 목록 조회
- 단일 일기 상세 조회
"""

import uuid
from datetime import date

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.diary import Diary
from app.models.diary_result import DiaryResult


async def create_diary(
    db: AsyncSession,
    user_id: uuid.UUID,
    content: str,
    written_date: date,
) -> Diary:
    """
    일기 생성
    - 동일 날짜에 이미 일기가 존재하면 is_overwrite=True로 업데이트
    """
    # 기존 일기 확인
    stmt = select(Diary).where(
        and_(Diary.user_id == user_id, Diary.written_date == written_date)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # 덮어쓰기: 기존 일기 내용 업데이트
        existing.content = content
        existing.is_overwrite = True
        await db.commit()
        await db.refresh(existing)
        return existing

    # 새 일기 생성
    diary = Diary(
        user_id=user_id,
        content=content,
        written_date=written_date,
    )
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return diary


async def get_diaries_by_month(
    db: AsyncSession,
    user_id: uuid.UUID,
    year: int,
    month: int,
) -> list[Diary]:
    """월별 일기 목록 조회 (날짜 내림차순)"""
    stmt = (
        select(Diary)
        .options(joinedload(Diary.result))
        .where(
            and_(
                Diary.user_id == user_id,
                extract("year", Diary.written_date) == year,
                extract("month", Diary.written_date) == month,
            )
        )
        .order_by(Diary.written_date.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_bookshelf_data(
    db: AsyncSession,
    user_id: uuid.UUID,
    year: int,
) -> list[dict]:
    """
    연간 책장 데이터 조회
    - 12개월 각각에 대해: 일기 수, AI 결과 존재 여부, 대표 스케치 URL
    - 대표 이미지 = 해당 월 가장 최근 AI 결과의 스케치
    """
    # 해당 연도 모든 일기 + 결과를 한 번에 조회
    stmt = (
        select(Diary)
        .options(joinedload(Diary.result))
        .where(
            and_(
                Diary.user_id == user_id,
                extract("year", Diary.written_date) == year,
            )
        )
        .order_by(Diary.written_date.desc())
    )
    result = await db.execute(stmt)
    diaries = list(result.scalars().unique().all())

    # 월별 그룹핑
    months_data: dict[int, dict] = {}
    for m in range(1, 13):
        months_data[m] = {
            "month": m,
            "diary_count": 0,
            "has_result": False,
            "cover_image_url": None,
            "cover_emotion_color": None,
            "cover_title": None,
        }

    for d in diaries:
        m = d.written_date.month
        months_data[m]["diary_count"] += 1

        # AI 결과가 있고 soft delete 되지 않은 경우
        if d.result and d.result.deleted_at is None:
            months_data[m]["has_result"] = True
            # 대표 이미지: 가장 최근 결과 (이미 날짜 내림차순 정렬됨)
            if months_data[m]["cover_image_url"] is None:
                months_data[m]["cover_image_url"] = d.result.sketch_image_url
                months_data[m]["cover_emotion_color"] = d.result.emotion_color
                months_data[m]["cover_title"] = d.result.poetic_title

    return [months_data[m] for m in range(1, 13)]


async def get_diary_by_id(
    db: AsyncSession,
    diary_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Diary | None:
    """일기 상세 조회 (결과 + 메모리 포함)"""
    stmt = (
        select(Diary)
        .options(joinedload(Diary.result), joinedload(Diary.memory))
        .where(and_(Diary.id == diary_id, Diary.user_id == user_id))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
