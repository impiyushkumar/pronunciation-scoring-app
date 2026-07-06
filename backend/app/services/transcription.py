# -----------------------------------------------------------------------
# Whisper STT — transcription with word-level timestamps + confidence
# -----------------------------------------------------------------------

import io
import logging
import tempfile
import os
from dataclasses import dataclass, field
from typing import List, Optional

from pydub import AudioSegment

from app.config import settings

logger = logging.getLogger("pronunciation-api.transcription")

# Lazy-loaded singleton — model is heavy, load once
_model = None


def _get_model():
    """Load the Whisper model once (singleton). Called on first transcription."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(
            f"Loading Whisper model: {settings.WHISPER_MODEL} "
            f"(compute_type={settings.WHISPER_COMPUTE_TYPE})"
        )
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device="cpu",
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
        logger.info("Whisper model loaded successfully")
    return _model


@dataclass
class WordInfo:
    """A single transcribed word with timing and confidence."""
    word: str
    start: float
    end: float
    probability: float  # 0.0 – 1.0


@dataclass
class TranscriptionResult:
    """Full transcription output."""
    words: List[WordInfo] = field(default_factory=list)
    full_text: str = ""
    language: str = ""
    language_probability: float = 0.0
    duration: float = 0.0


class TranscriptionError(Exception):
    """Raised when transcription fails — carries a user-friendly message."""
    pass


def transcribe_audio(audio: AudioSegment) -> TranscriptionResult:
    """
    Transcribe audio using faster-whisper with word-level timestamps.

    Args:
        audio: Decoded AudioSegment from the validator.

    Returns:
        TranscriptionResult with words, language, confidence scores.

    Raises:
        TranscriptionError with clean user-facing message.
    """
    model = _get_model()

    # Export audio to a temp WAV file (faster-whisper reads files, not streams)
    tmp_path = None
    try:
        # Convert to 16kHz mono WAV (what Whisper expects)
        audio_16k = audio.set_frame_rate(16000).set_channels(1)

        # Write to temp file
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(tmp_fd)
        audio_16k.export(tmp_path, format="wav")

        # Transcribe — don't specify language so we get detection
        segments, info = model.transcribe(
            tmp_path,
            word_timestamps=True,
            beam_size=1,  # minimize memory usage
        )

        result = TranscriptionResult(
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
        )

        # Collect all words from all segments
        all_words = []
        text_parts = []

        for segment in segments:
            text_parts.append(segment.text.strip())
            if segment.words:
                for w in segment.words:
                    all_words.append(WordInfo(
                        word=w.word.strip(),
                        start=round(w.start, 2),
                        end=round(w.end, 2),
                        probability=round(w.probability, 4),
                    ))

        result.words = all_words
        result.full_text = " ".join(text_parts).strip()

        logger.info(
            f"Transcription complete: {len(all_words)} words, "
            f"lang={info.language} ({info.language_probability:.2f}), "
            f"duration={info.duration:.1f}s"
        )

        return result

    except TranscriptionError:
        raise
    except Exception as e:
        logger.exception("Transcription failed")
        raise TranscriptionError(
            "Failed to transcribe the audio. Please try a clearer recording."
        )
    finally:
        # Clean up temp file — no audio persists beyond request
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def check_transcription_quality(result: TranscriptionResult) -> Optional[str]:
    """
    Check transcription result for edge cases. Returns a warning/error
    message if there's an issue, or None if everything looks fine.
    """
    # --- Non-English ---
    if result.language != "en" and result.language_probability > 0.7:
        return (
            f"This app only scores English pronunciation. "
            f"Detected language: {result.language} "
            f"(confidence: {result.language_probability:.0%})."
        )

    # --- Empty / silence ---
    if not result.words or not result.full_text.strip():
        return (
            "No speech detected in the audio. "
            "Please upload a recording with clear English speech."
        )

    # --- Very few words (likely silence with brief noise) ---
    if len(result.words) < 3:
        return (
            "Very little speech detected. "
            "Please upload a recording with at least a few sentences of English speech."
        )

    return None


def get_quality_warnings(result: TranscriptionResult) -> List[str]:
    """
    Generate non-blocking warnings about audio quality.
    These don't prevent scoring but are shown to the user.
    """
    warnings = []

    if not result.words:
        return warnings

    # Average confidence
    avg_conf = sum(w.probability for w in result.words) / len(result.words)

    if avg_conf < 0.5:
        warnings.append(
            "Audio quality significantly affected scoring accuracy. "
            "Background noise or unclear speech reduced overall confidence."
        )
    elif avg_conf < 0.7:
        warnings.append(
            "Some background noise or unclear sections detected. "
            "Confidence scores may be lower than expected."
        )

    # Check for many low-confidence words
    low_conf_count = sum(1 for w in result.words if w.probability < settings.CONFIDENCE_LOW)
    low_conf_pct = low_conf_count / len(result.words)

    if low_conf_pct > 0.5:
        warnings.append(
            f"{low_conf_count} of {len(result.words)} words had low confidence. "
            "Consider recording in a quieter environment."
        )

    return warnings
