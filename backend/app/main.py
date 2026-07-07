from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import time
import logging

from app.models import (
    HealthResponse,
    AnalysisResponse,
    ErrorResponse,
)
from app.config import settings
from app.middleware.rate_limiter import limiter, rate_limit_handler
from app.services.audio_validator import validate_audio, AudioValidationError
from app.services.transcription import (
    transcribe_audio,
    check_transcription_quality,
    get_quality_warnings,
    TranscriptionError,
)
from app.services.phoneme_analyzer import get_phonemes_for_words
from app.services.scorer import build_word_results, calculate_score
from app.services.llm_analyzer import analyze_with_llm, apply_llm_classifications

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("pronunciation-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Pronunciation Scoring API",
    description="Scores English pronunciation from free-form speech audio.",
    version="0.3.0",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will lock down to Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers — never leak stack traces
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred. Please try again.",
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=str(exc.detail),
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway + frontend cold-start detection."""
    return HealthResponse(
        status="ok",
        timestamp=time.time(),
        version="0.3.0",
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
@limiter.limit(settings.RATE_LIMIT)
async def analyze_audio(request: Request, file: UploadFile = File(...)):
    """
    Full pronunciation analysis pipeline:
    1. Validate audio (MIME, decode, duration, size)
    2. Transcribe with Whisper (word timestamps + confidence)
    3. Check transcription quality (language, silence, noise)
    4. G2P phoneme conversion
    5. LLM error classification + feedback (Gemini Flash)
    6. Score and classify errors (LLM-enhanced or heuristic fallback)
    7. Return results — then discard all audio data
    """
    contents = None
    try:
        # ---- Read file ----
        contents = await file.read()

        logger.info(
            f"Received file: {file.filename}, "
            f"content_type={file.content_type}, "
            f"size={len(contents) / 1024:.1f}KB"
        )

        # ---- 1. Validate audio ----
        try:
            audio_segment = validate_audio(contents, file.filename or "unknown")
        except AudioValidationError as e:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="validation_error",
                    message=str(e),
                ).model_dump(),
            )

        # Audio bytes no longer needed — free memory
        del contents
        contents = None

        # ---- 2. Transcribe ----
        try:
            transcription = transcribe_audio(audio_segment)
        except TranscriptionError as e:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="transcription_error",
                    message=str(e),
                ).model_dump(),
            )

        # AudioSegment no longer needed
        del audio_segment

        # ---- 3. Quality checks ----
        quality_issue = check_transcription_quality(transcription)
        if quality_issue:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="quality_error",
                    message=quality_issue,
                ).model_dump(),
            )

        warnings = get_quality_warnings(transcription)

        # ---- 4. G2P phonemes ----
        phoneme_map = get_phonemes_for_words(transcription.words)

        # ---- 5. LLM analysis (optional — graceful fallback) ----
        llm_word_errors = None
        llm_feedback = None

        llm_result = analyze_with_llm(
            transcription.words,
            transcription.full_text,
            phoneme_map,
        )

        if llm_result:
            llm_word_errors, llm_feedback, _ = apply_llm_classifications(
                transcription.words, llm_result
            )
            logger.info("Using LLM-enhanced classifications")
        else:
            logger.info("Using heuristic classifications (LLM unavailable)")

        # ---- 6. Score ----
        word_results = build_word_results(
            transcription.words, phoneme_map, llm_word_errors
        )
        score, heuristic_feedback = calculate_score(
            transcription.words,
            transcription.duration,
        )

        # Use LLM feedback if available, otherwise heuristic
        feedback = llm_feedback if llm_feedback else heuristic_feedback

        # ---- 7. Return results ----
        return AnalysisResponse(
            score=score,
            words=word_results,
            feedback=feedback,
            warnings=warnings,
            transcript=transcription.full_text,
            language=transcription.language,
        )

    except Exception:
        # Global handler will catch this, but explicit cleanup first
        raise
    finally:
        # Ensure audio is always discarded — DPDP compliance
        if contents is not None:
            del contents
