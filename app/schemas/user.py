"""
사용자 API 응답 스키마
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
