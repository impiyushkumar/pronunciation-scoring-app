from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.models import (
    HealthResponse,
    WordResult,
    AnalysisResponse,
    ErrorResponse,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("pronunciation-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Pronunciation Scoring API",
    description="Scores English pronunciation from free-form speech audio.",
    version="0.1.0",
)

# CORS — allow the Vercel frontend (and localhost for dev)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Vercel preview/production URLs added here or via env var later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1: permissive; will lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces
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
        version="0.1.0",
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Phase 1 STUB — accepts an audio file upload and returns dummy data.
    Verifies the full upload round-trip works before real logic is added.
    """
    # Read the file to confirm upload actually works
    contents = await file.read()
    file_size_kb = len(contents) / 1024

    logger.info(
        f"Received file: {file.filename}, "
        f"content_type={file.content_type}, "
        f"size={file_size_kb:.1f}KB"
    )

    # Explicit cleanup — audio never persists beyond request
    del contents

    # Return stub response
    return AnalysisResponse(
        score=82.5,
        words=[
            WordResult(
                word="Hello",
                start=0.00,
                end=0.42,
                confidence=0.96,
                phonemes="HH AH0 L OW1",
            ),
            WordResult(
                word="my",
                start=0.44,
                end=0.58,
                confidence=0.91,
                phonemes="M AY1",
            ),
            WordResult(
                word="name",
                start=0.60,
                end=0.88,
                confidence=0.88,
                phonemes="N EY1 M",
            ),
            WordResult(
                word="is",
                start=0.90,
                end=1.02,
                confidence=0.94,
                phonemes="IH1 Z",
            ),
            WordResult(
                word="pronunciation",
                start=1.10,
                end=1.85,
                confidence=0.63,
                error_type="unclear",
                phonemes="P R AH0 N AH2 N S IY0 EY1 SH AH0 N",
            ),
            WordResult(
                word="scoring",
                start=1.90,
                end=2.30,
                confidence=0.45,
                error_type="mispronunciation",
                phonemes="S K AO1 R IH0 NG",
            ),
        ],
        feedback=(
            "This is a stub response for Phase 1 deployment verification. "
            "Real pronunciation analysis will be available in Phase 2. "
            "The word 'pronunciation' was flagged as unclear, and 'scoring' "
            "was flagged as a potential mispronunciation."
        ),
        warnings=[],
        transcript="Hello my name is pronunciation scoring",
        language="en",
    )
