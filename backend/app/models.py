from pydantic import BaseModel
from typing import List, Optional


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str


class WordResult(BaseModel):
    """A single word from the transcript with scoring metadata."""
    word: str
    start: float
    end: float
    confidence: float
    error_type: Optional[str] = None  # "mispronunciation" | "unclear" | "omission" | None
    phonemes: Optional[str] = None    # ARPAbet representation


class AnalysisResponse(BaseModel):
    """Full analysis result returned to the frontend."""
    score: float                    # 0-100 overall pronunciation score
    words: List[WordResult]         # per-word results
    feedback: str                   # LLM-generated feedback text
    warnings: List[str]             # quality/confidence warnings
    transcript: str                 # full transcript text
    language: Optional[str] = None  # detected language code


class ErrorResponse(BaseModel):
    """Structured error response — no raw stack traces."""
    error: str       # machine-readable error code
    message: str     # human-readable message
    detail: Optional[str] = None
