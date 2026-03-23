"""
개발 서버 실행 스크립트
- 실행: python main.py 또는 uv run python main.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
