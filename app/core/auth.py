"""
인증 모듈
- Google ID Token 검증 → 유저 조회/자동 생성
- FastAPI Depends()로 엔드포인트에 주입
- DEBUG 모드에서는 X-Dev-User-Id 헤더로 인증 우회 가능
"""

import logging

from fastapi import Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Google 공개키 요청용 (캐싱됨)
_google_request = google_requests.Request()


async def _get_or_create_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Google ID로 유저 조회, 없으면 자동 생성"""
    stmt = select(User).where(User.google_id == google_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"New user created: {email}")

    return user


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authorization: Bearer <google_id_token> 헤더에서 토큰 추출 → 검증 → 유저 반환
    DEBUG 모드: X-Dev-User-Id 헤더로 google_id 직접 지정 가능
    """

    # === 개발 모드 우회 ===
    if settings.DEBUG:
        dev_user_id = request.headers.get("X-Dev-User-Id")
        if dev_user_id:
            stmt = select(User).where(User.google_id == dev_user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user
            # dev user가 없으면 자동 생성
            return await _get_or_create_user(
                db,
                google_id=dev_user_id,
                email=f"{dev_user_id}@dev.local",
                name="Dev User",
            )

    # === Authorization 헤더 추출 ===
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
        )

    token = auth_header.split(" ", 1)[1]

    # === Google ID Token 검증 ===
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            _google_request,
        )
    except ValueError as e:
        logger.warning(f"Invalid Google ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # === 유저 조회/생성 ===
    return await _get_or_create_user(
        db,
        google_id=id_info["sub"],
        email=id_info.get("email", ""),
        name=id_info.get("name"),
        avatar_url=id_info.get("picture"),
    )
