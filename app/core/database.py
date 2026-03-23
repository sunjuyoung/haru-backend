"""
데이터베이스 세션 관리
- SQLAlchemy 2.0 async 엔진 + 세션 팩토리
- FastAPI Depends()를 통해 요청별 세션 주입
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # DEBUG 모드에서만 SQL 로그 출력
    pool_size=5,
    max_overflow=10,
)

# 세션 팩토리
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# SQLAlchemy 모델 베이스 클래스
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션 제네레이터"""
    async with async_session() as session:
        yield session
