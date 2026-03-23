"""
API v1 라우터 통합
- 모든 v1 엔드포인트를 하나의 라우터로 묶는다
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.diaries import router as diaries_router

v1_router = APIRouter(prefix="/api/v1")

# === 헬스체크 ===
v1_router.include_router(health_router)

# === 일기 CRUD ===
v1_router.include_router(diaries_router)
