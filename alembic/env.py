"""
Alembic 환경 설정 (비동기 asyncpg 지원)
- settings에서 DATABASE_URL을 가져와 동적으로 연결
- autogenerate 시 Base.metadata를 참조하여 마이그레이션 자동 생성
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — autogenerate가 모든 테이블을 감지하도록 임포트

# Alembic Config 객체
config = context.config

# alembic.ini의 sqlalchemy.url을 settings 값으로 오버라이드
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate 지원을 위한 metadata 등록
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드 마이그레이션 (SQL 스크립트만 생성)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """마이그레이션 실행 (동기 컨텍스트)"""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 엔진으로 마이그레이션 실행"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """온라인 모드 마이그레이션 (비동기 엔진 사용)"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
