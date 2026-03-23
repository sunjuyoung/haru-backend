"""
FastAPI 애플리케이션 진입점
- CORS 미들웨어 설정
- API v1 라우터 등록
- 로컬 이미지 저장 시 정적 파일 서빙
- 실행: uvicorn app.main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS 미들웨어 (프론트엔드 localhost:3000 허용) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API 라우터 등록 ===
app.include_router(v1_router)

# === 로컬 이미지 정적 파일 서빙 (R2 미설정 시) ===
_uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
_uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")
