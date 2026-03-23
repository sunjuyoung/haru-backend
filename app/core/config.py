"""
애플리케이션 설정 모듈
- .env 파일에서 환경변수를 자동으로 로드
- pydantic-settings로 타입 안전한 설정 관리
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === 앱 기본 설정 ===
    APP_NAME: str = "하루일기 API"
    DEBUG: bool = False

    # === 데이터베이스 ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:rnrdj123@localhost:5433/haru"

    # === CORS (Sprint 6에서 프로덕션 도메인 추가) ===
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # === AI 파이프라인 (Sprint 2에서 사용) ===
    OPENAI_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""

    # === R2 스토리지 (Sprint 2에서 사용) ===
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "haru-sketches"
    R2_PUBLIC_URL: str = ""  # R2 퍼블릭 도메인 (예: https://pub-xxx.r2.dev)

    # === 에이전트 실행 설정 (v2.3) ===
    AGENT_TIMEOUT_SECONDS: int = 30
    AGENT_MAX_WORKERS: int = 4


settings = Settings()
