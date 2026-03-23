"""
Cloudflare R2 클라이언트 모듈
- S3 호환 API로 이미지 업로드/삭제
- 외부 URL에서 이미지를 다운로드하여 R2에 업로드
"""

import urllib.request

import boto3
from botocore.config import Config

from app.core.config import settings


def _get_r2_client():
    """R2 S3 호환 클라이언트 생성"""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_image_from_url(source_url: str, filename: str) -> str:
    """
    외부 URL에서 이미지를 다운로드하여 R2에 업로드

    Args:
        source_url: 다운로드할 이미지 URL (예: Replicate 임시 URL)
        filename: R2 내 저장 경로 (예: sketches/uuid.webp)

    Returns:
        R2 퍼블릭 URL
    """
    # 이미지 다운로드
    req = urllib.request.Request(source_url, headers={"User-Agent": "haru-server/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        image_data = response.read()

    # R2에 업로드
    client = _get_r2_client()
    content_type = "image/webp" if filename.endswith(".webp") else "image/png"
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
    )

    return f"{settings.R2_PUBLIC_URL}/{filename}"


def upload_image_bytes(image_data: bytes, filename: str, content_type: str = "image/webp") -> str:
    """
    바이트 데이터를 R2에 직접 업로드

    Args:
        image_data: 이미지 바이트 데이터
        filename: R2 내 저장 경로
        content_type: MIME 타입

    Returns:
        R2 퍼블릭 URL
    """
    client = _get_r2_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
    )

    return f"{settings.R2_PUBLIC_URL}/{filename}"


def delete_image(filename: str) -> None:
    """R2에서 이미지 삭제"""
    client = _get_r2_client()
    client.delete_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=filename,
    )
