"""
일기 CRUD + AI 생성 API 라우터
- POST   /api/v1/diaries              일기 생성
- GET    /api/v1/diaries              월별 일기 목록
- GET    /api/v1/diaries/{id}         일기 상세
- POST   /api/v1/diaries/{id}/generate  AI 생성 (SSE 스트리밍)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.diary import (
    BookshelfMonth,
    BookshelfResponse,
    DiaryCreate,
    DiaryDetailResponse,
    DiaryListItem,
    DiaryListResponse,
    DiaryResponse,
)
from app.services.diary_service import (
    create_diary,
    get_bookshelf_data,
    get_diaries_by_month,
    get_diary_by_id,
)
from app.services.generation_service import diary_generation_stream

router = APIRouter(prefix="/diaries", tags=["diaries"])


@router.post("", response_model=DiaryResponse, status_code=status.HTTP_201_CREATED)
async def create_diary_endpoint(
    body: DiaryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    일기 생성
    - 동일 날짜에 이미 일기가 있으면 덮어쓰기 (is_overwrite=True)
    """
    diary = await create_diary(
        db=db,
        user_id=current_user.id,
        content=body.content,
        written_date=body.written_date,
    )
    return diary


@router.get("", response_model=DiaryListResponse)
async def list_diaries_endpoint(
    year: int = Query(..., ge=2020, le=2100, description="조회 연도"),
    month: int = Query(..., ge=1, le=12, description="조회 월"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """월별 일기 목록 조회"""
    diaries = await get_diaries_by_month(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

    items = [
        DiaryListItem(
            id=d.id,
            written_date=d.written_date,
            content_preview=d.content[:50],
            is_overwrite=d.is_overwrite,
            has_result=d.result is not None and d.result.deleted_at is None,
            created_at=d.created_at,
        )
        for d in diaries
    ]

    return DiaryListResponse(
        year=year,
        month=month,
        diaries=items,
        total=len(items),
    )


@router.get("/bookshelf", response_model=BookshelfResponse)
async def bookshelf_endpoint(
    year: int = Query(..., ge=2020, le=2100, description="조회 연도"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    책장 갤러리 — 연간 12개월 책장 데이터
    - 월별 일기 수, AI 결과 존재 여부, 대표 스케치 URL
    """
    months = await get_bookshelf_data(db=db, user_id=current_user.id, year=year)
    return BookshelfResponse(
        year=year,
        months=[BookshelfMonth(**m) for m in months],
    )


@router.get("/{diary_id}", response_model=DiaryDetailResponse)
async def get_diary_endpoint(
    diary_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """일기 상세 조회 (AI 생성 결과 포함)"""
    diary = await get_diary_by_id(
        db=db,
        diary_id=diary_id,
        user_id=current_user.id,
    )

    if diary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found",
        )

    return diary


@router.post("/{diary_id}/generate")
async def generate_diary_endpoint(
    diary_id: uuid.UUID,
    force: bool = Query(False, description="이미 결과가 있어도 재생성 (덮어쓰기)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI 생성 트리거 — SSE 스트리밍 응답
    - 감정 분석 → 시 + 스케치 (+ 조건부 memory) 병렬 생성 → DB 저장
    - force=true: 기존 결과를 soft delete 후 재생성 (덮어쓰기)
    """
    diary = await get_diary_by_id(
        db=db,
        diary_id=diary_id,
        user_id=current_user.id,
    )

    if diary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found",
        )

    # 이미 결과가 있고 force가 아닌 경우 → 409 반환
    if diary.result is not None and diary.result.deleted_at is None and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 AI 생성 결과가 있습니다. 재생성하려면 force=true를 사용하세요.",
        )

    return StreamingResponse(
        diary_generation_stream(db=db, diary=diary),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
