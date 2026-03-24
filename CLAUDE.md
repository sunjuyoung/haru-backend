### 궁금한점 은 언제든지 물어봐주세요!

### 주석을 기능 별로 달아주세요

### git

- https://github.com/sunjuyoung/haru-backend.git, branch `main`
- 주요 기능 추가 시 `feat: [기능명]` 커밋 메시지
- gitignore 적절하게 설정 (node_modules, .env 등)

### database

DATABASE_URL: str = "postgresql+asyncpg://postgres:rnrdj123@localhost:5433/haru"

---

## CrewAI Agent 아키텍처

### Agent 역할 (4개 AI Agent + 1 서비스)

| Agent            | 역할               | 설명                                                                                       |
| ---------------- | ------------------ | ------------------------------------------------------------------------------------------ |
| 감정 분석 전문가 | `emotion_agent.py` | 일기 텍스트에서 감정, 키워드, 분위기, 색상, 후회 점수 분석                                 |
| 시인             | `poet_agent.py`    | 감정 기반 시적 제목(≤15자) + 4~6행 자유시 생성                                             |
| 아트 디렉터      | `art_agent.py`     | 감정을 연필 스케치 이미지 프롬프트로 변환 → Replicate FLUX.1 Pro로 이미지 생성 → R2 업로드 |
| 기억 리라이터    | `memory_agent.py`  | 후회 점수 ≥ 0.3일 때만 실행. "만약 다르게 했다면?" 따뜻한 가상 이야기 + 수채화 이미지 생성 |
| 사운드 매칭      | `sound.py`         | 감정 → ASMR 사운드 매핑 (현재 기본값 반환)                                                 |

### Models

- **LLM**: `gpt-4o` (Production) / `gpt-4o-mini` (DEBUG)
- **이미지 생성**: Replicate `black-forest-labs/flux-1.1-pro` (512x512, WebP)
- **스토리지**: Cloudflare R2

### 파이프라인 흐름

```
POST /api/v1/diaries/{id}/generate (SSE 스트리밍)

[1] 감정 분석 (직렬, 필수) ─── 실패 시 파이프라인 중단
         │
[2] 병렬 실행 ─────────────────────────────────
    ├─ 시인 (60s)         ─── 필수
    ├─ 아트 디렉터 (120s) ─── 필수
    └─ 기억 리라이터 (180s) ─ 선택 (regret ≥ 0.3)
         │
[3] 사운드 매칭 + DB 저장 (Atomic)
```

### 주요 설정

- `AGENT_TIMEOUT_SECONDS`: 30s (기본)
- `AGENT_MAX_WORKERS`: 4 (ThreadPoolExecutor)
- 기존 결과 덮어쓰기 시 Soft Delete 후 재생성
