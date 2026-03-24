"""
사운드 매칭 서비스
- 감정(primary_emotion) → ASMR 사운드 키 매핑
- Phase 1: 정적 딕셔너리 기반
- Phase 2: AI 기반 사운드 생성 (Suno API 등) 검토 예정
"""

# === 감정별 사운드 매핑 ===

SOUND_MAP: dict[str, str] = {
    "joy":        "pencil_bright.mp3",
    "sadness":    "pencil_slow.mp3",
    "anger":      "pencil_sharp.mp3",
    "fear":       "pencil_trembling.mp3",
    "regret":     "pencil_erasing.mp3",
    "calm":       "pencil_gentle.mp3",
    "excitement": "pencil_fast.mp3",
    "love":       "pencil_gentle.mp3",
    "anxiety":    "pencil_trembling.mp3",
    "loneliness": "pencil_slow.mp3",
    "hope":       "pencil_bright.mp3",
    "gratitude":  "pencil_gentle.mp3",
}

DEFAULT_SOUND = "pencil_default.mp3"


def match_sound(primary_emotion: str) -> str:
    """
    감정에 맞는 사운드 키 반환

    [임시] 현재 pencil_default.mp3만 존재하므로 항상 기본 사운드 반환
    TODO: 사운드 에셋 추가 후 아래 매칭 로직 복원
    """
    # [임시] 모든 감정에 pencil_default.mp3 사용
    return DEFAULT_SOUND

    # --- 아래는 사운드 에셋 추가 후 복원할 로직 ---
    # emotion_lower = primary_emotion.lower().strip()
    # if emotion_lower in SOUND_MAP:
    #     return SOUND_MAP[emotion_lower]
    # for key in SOUND_MAP:
    #     if key in emotion_lower:
    #         return SOUND_MAP[key]
    # return DEFAULT_SOUND
