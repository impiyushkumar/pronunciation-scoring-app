# -----------------------------------------------------------------------
# Audio file validation — server-side (never trust the client)
# -----------------------------------------------------------------------

import io
import logging
from typing import Tuple

import filetype
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from app.config import settings

logger = logging.getLogger("pronunciation-api.validator")

ALLOWED_MIME_PREFIXES = ("audio/",)
ALLOWED_MIME_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/ogg", "audio/flac", "audio/mp4", "audio/x-m4a",
    "audio/aac", "audio/webm", "audio/vnd.dlna.adts",
    "video/mp4",  # some .m4a files report as video/mp4
}


class AudioValidationError(Exception):
    """Raised when audio validation fails — carries a user-friendly message."""
    pass


def validate_audio(file_bytes: bytes, filename: str) -> AudioSegment:
    """
    Validate uploaded audio bytes. Returns the decoded AudioSegment on success.
    Raises AudioValidationError with a clean user-facing message on failure.

    Checks (in order):
    1. File size (≤ MAX_FILE_SIZE_MB)
    2. MIME type via magic bytes (not extension)
    3. Actual decode (catches corruption)
    4. Duration bounds (MIN_DURATION_S – MAX_DURATION_S)
    """
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    # --- 1. Size ---
    if len(file_bytes) > max_bytes:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise AudioValidationError(
            f"File size must be under {settings.MAX_FILE_SIZE_MB} MB. "
            f"Yours is {size_mb:.1f} MB."
        )

    if len(file_bytes) == 0:
        raise AudioValidationError("The uploaded file is empty.")

    # --- 2. MIME type via magic bytes ---
    kind = filetype.guess(file_bytes)
    if kind is None:
        raise AudioValidationError(
            "Could not determine the file type. "
            "Please upload a valid audio file (MP3, WAV, M4A, OGG, FLAC)."
        )

    mime = kind.mime
    logger.info(f"Detected MIME: {mime} for file: {filename}")

    is_audio = mime.startswith("audio/") or mime in ALLOWED_MIME_TYPES
    if not is_audio:
        raise AudioValidationError(
            f"This doesn't appear to be an audio file (detected: {mime}). "
            "Please upload MP3, WAV, M4A, OGG, or FLAC."
        )

    # --- 3. Decode audio (catches corruption) ---
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes))
    except CouldntDecodeError:
        raise AudioValidationError(
            "This audio file appears to be corrupted or in an unsupported format. "
            "Please try another recording."
        )
    except Exception as e:
        logger.warning(f"Audio decode failed: {e}")
        raise AudioValidationError(
            "Could not process this audio file. "
            "Please try a different file or format."
        )

    # --- 4. Duration ---
    duration_s = audio.duration_seconds

    if duration_s < settings.MIN_DURATION_S:
        raise AudioValidationError(
            f"Audio must be {settings.MIN_DURATION_S}–{settings.MAX_DURATION_S} seconds. "
            f"Yours is {duration_s:.0f} seconds."
        )

    if duration_s > settings.MAX_DURATION_S:
        raise AudioValidationError(
            f"Audio must be {settings.MIN_DURATION_S}–{settings.MAX_DURATION_S} seconds. "
            f"Yours is {duration_s:.0f} seconds."
        )

    logger.info(f"Audio validated: {duration_s:.1f}s, {mime}, {len(file_bytes)} bytes")
    return audio
