"""
이미지 저장 모듈 — 로컬/R2 자동 선택
- R2 설정이 있으면 Cloudflare R2에 업로드
- R2 설정이 없으면 로컬 파일시스템에 저장 + FastAPI StaticFiles로 서빙
"""

import os
import urllib.request
from pathlib import Path

from app.core.config import settings

# 로컬 저장 디렉토리 (server/uploads/)
_LOCAL_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# R2 설정이 있는지 확인
_USE_R2 = bool(settings.R2_ACCOUNT_ID and settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY)


def _ensure_local_dir(filename: str) -> Path:
    """로컬 저장 경로 생성"""
    filepath = _LOCAL_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    return filepath


def _download_image(source_url: str) -> bytes:
    """외부 URL에서 이미지 다운로드"""
    req = urllib.request.Request(source_url, headers={"User-Agent": "haru-server/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


# === 로컬 저장 함수 ===

def _local_upload_from_url(source_url: str, filename: str) -> str:
    """외부 URL → 로컬 파일 저장"""
    image_data = _download_image(source_url)
    filepath = _ensure_local_dir(filename)
    filepath.write_bytes(image_data)
    return f"http://localhost:8000/uploads/{filename}"


def _local_upload_bytes(image_data: bytes, filename: str) -> str:
    """바이트 데이터 → 로컬 파일 저장"""
    filepath = _ensure_local_dir(filename)
    filepath.write_bytes(image_data)
    return f"http://localhost:8000/uploads/{filename}"


def _local_delete(filename: str) -> None:
    """로컬 파일 삭제"""
    filepath = _LOCAL_DIR / filename
    if filepath.exists():
        filepath.unlink()


# === R2 저장 함수 ===

def _get_r2_client():
    """R2 S3 호환 클라이언트 생성"""
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _r2_upload_from_url(source_url: str, filename: str) -> str:
    """외부 URL → R2 업로드"""
    image_data = _download_image(source_url)
    client = _get_r2_client()
    content_type = "image/webp" if filename.endswith(".webp") else "image/png"
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
    )
    return f"{settings.R2_PUBLIC_URL}/{filename}"


def _r2_upload_bytes(image_data: bytes, filename: str, content_type: str = "image/webp") -> str:
    """바이트 데이터 → R2 업로드"""
    client = _get_r2_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
    )
    return f"{settings.R2_PUBLIC_URL}/{filename}"


def _r2_delete(filename: str) -> None:
    """R2 파일 삭제"""
    client = _get_r2_client()
    client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=filename)


# === 공개 API — R2/로컬 자동 선택 ===

def upload_image_from_url(source_url: str, filename: str) -> str:
    """외부 URL에서 이미지를 다운로드하여 저장 (R2 또는 로컬)"""
    if _USE_R2:
        return _r2_upload_from_url(source_url, filename)
    return _local_upload_from_url(source_url, filename)


def upload_image_bytes(image_data: bytes, filename: str, content_type: str = "image/webp") -> str:
    """바이트 데이터를 저장 (R2 또는 로컬)"""
    if _USE_R2:
        return _r2_upload_bytes(image_data, filename, content_type)
    return _local_upload_bytes(image_data, filename)


def delete_image(filename: str) -> None:
    """이미지 삭제 (R2 또는 로컬)"""
    if _USE_R2:
        _r2_delete(filename)
    else:
        _local_delete(filename)
