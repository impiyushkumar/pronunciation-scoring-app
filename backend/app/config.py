# -----------------------------------------------------------------------
# App configuration — reads from environment variables
# -----------------------------------------------------------------------

import os
from typing import List


class Settings:
    """Central configuration, loaded from environment variables."""

    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Whisper ---
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "tiny")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # --- Audio validation ---
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    MIN_DURATION_S: int = int(os.getenv("MIN_DURATION_S", "30"))
    MAX_DURATION_S: int = int(os.getenv("MAX_DURATION_S", "45"))

    # --- Rate limiting ---
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "5/minute")

    # --- CORS ---
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    ]

    # --- Scoring thresholds ---
    CONFIDENCE_HIGH: float = 0.85
    CONFIDENCE_MEDIUM: float = 0.70
    CONFIDENCE_LOW: float = 0.50


settings = Settings()
