"""
SSE(Server-Sent Events) 헬퍼
- FastAPI StreamingResponse에서 사용하는 이벤트 포맷 생성
"""

import json
from typing import Any


def sse_event(event: str, data: Any = None) -> str:
    """
    SSE 이벤트 문자열 생성

    Args:
        event: 이벤트 타입 (예: "started", "step:analyzing", "complete", "error")
        data: 이벤트 데이터 (dict → JSON 직렬화)

    Returns:
        SSE 포맷 문자열 ("event: ...\ndata: ...\n\n")
    """
    lines = [f"event: {event}"]

    if data is not None:
        if isinstance(data, (dict, list)):
            lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        else:
            lines.append(f"data: {data}")

    return "\n".join(lines) + "\n\n"
