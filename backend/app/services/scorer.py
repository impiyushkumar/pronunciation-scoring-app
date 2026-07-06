# -----------------------------------------------------------------------
# Scoring engine — computes pronunciation score from STT + G2P data
# -----------------------------------------------------------------------

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.models import WordResult
from app.services.transcription import WordInfo

logger = logging.getLogger("pronunciation-api.scorer")


def classify_word_error(word: WordInfo) -> Optional[str]:
    """
    Heuristic error classification based on confidence thresholds.
    Phase 2 uses thresholds; Phase 3 will add LLM-based classification.

    Returns: "mispronunciation" | "unclear" | None
    """
    if word.probability < settings.CONFIDENCE_LOW:
        return "mispronunciation"
    elif word.probability < settings.CONFIDENCE_MEDIUM:
        return "unclear"
    return None


def build_word_results(
    words: List[WordInfo],
    phoneme_map: Dict[str, str],
) -> List[WordResult]:
    """
    Build the final word results list with error classifications and phonemes.
    """
    results = []

    for w in words:
        cleaned = re.sub(r"[^\w']", "", w.word).strip().lower()
        error_type = classify_word_error(w)
        phonemes = phoneme_map.get(cleaned)

        results.append(WordResult(
            word=w.word,
            start=w.start,
            end=w.end,
            confidence=round(w.probability, 4),
            error_type=error_type,
            phonemes=phonemes,
        ))

    return results


def calculate_score(
    words: List[WordInfo],
    duration: float,
) -> Tuple[float, str]:
    """
    Calculate overall pronunciation score (0–100).

    Formula:
        score = 0.50 × word_confidence_score
              + 0.25 × clarity_score
              + 0.15 × fluency_score
              + 0.10 × completeness_score

    Returns: (score, feedback_text)
    """
    if not words:
        return 0.0, "No speech detected to score."

    # ---- 1. Word confidence score (avg probability, scaled 0–100) ----
    avg_confidence = sum(w.probability for w in words) / len(words)
    word_confidence_score = avg_confidence * 100

    # ---- 2. Clarity score (% of words above threshold, scaled 0–100) ----
    clear_words = sum(1 for w in words if w.probability >= settings.CONFIDENCE_MEDIUM)
    clarity_score = (clear_words / len(words)) * 100

    # ---- 3. Fluency score (based on gaps between words) ----
    fluency_score = _calculate_fluency(words, duration)

    # ---- 4. Completeness score (penalize very short transcripts) ----
    # Expect ~2-3 words per second for natural speech
    expected_words = duration * 2.0  # conservative: 2 words/sec
    completeness = min(len(words) / max(expected_words, 1), 1.0)
    completeness_score = completeness * 100

    # ---- Weighted total ----
    score = (
        0.50 * word_confidence_score
        + 0.25 * clarity_score
        + 0.15 * fluency_score
        + 0.10 * completeness_score
    )

    # Clamp to 0–100
    score = max(0.0, min(100.0, round(score, 1)))

    # ---- Generate feedback ----
    feedback = _generate_feedback(
        score, words, avg_confidence, clarity_score, fluency_score
    )

    logger.info(
        f"Score: {score} (conf={word_confidence_score:.1f}, "
        f"clarity={clarity_score:.1f}, fluency={fluency_score:.1f}, "
        f"completeness={completeness_score:.1f})"
    )

    return score, feedback


def _calculate_fluency(words: List[WordInfo], duration: float) -> float:
    """
    Fluency score based on pauses/gaps between words.
    Natural speech has small gaps (< 0.5s). Long gaps = hesitations.
    """
    if len(words) < 2:
        return 50.0  # can't judge fluency from 1 word

    gaps = []
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap > 0:
            gaps.append(gap)

    if not gaps:
        return 80.0  # no measurable gaps

    avg_gap = sum(gaps) / len(gaps)
    long_pauses = sum(1 for g in gaps if g > 1.0)  # pauses > 1 second

    # Penalize long average gap and frequent long pauses
    gap_penalty = min(avg_gap / 1.0, 1.0) * 30  # max 30 point penalty
    pause_penalty = min(long_pauses / max(len(gaps), 1), 1.0) * 20  # max 20 point penalty

    fluency = max(0.0, 100.0 - gap_penalty - pause_penalty)
    return fluency


def _generate_feedback(
    score: float,
    words: List[WordInfo],
    avg_confidence: float,
    clarity_score: float,
    fluency_score: float,
) -> str:
    """
    Generate human-readable feedback based on scores.
    Phase 2: heuristic; Phase 3 will use Gemini for richer feedback.
    """
    parts = []

    # Overall impression
    if score >= 85:
        parts.append("Excellent pronunciation! Your speech was clear and well-articulated.")
    elif score >= 70:
        parts.append("Good pronunciation overall. There are a few areas for improvement.")
    elif score >= 50:
        parts.append("Fair pronunciation. Several words could use more practice.")
    else:
        parts.append("Your pronunciation needs work. Consider practicing individual words slowly.")

    # Specific feedback on problem areas
    problem_words = [w for w in words if w.probability < settings.CONFIDENCE_MEDIUM]
    if problem_words:
        worst = sorted(problem_words, key=lambda w: w.probability)[:5]
        word_list = ", ".join(f"'{w.word.strip()}'" for w in worst)
        parts.append(f"Words to practice: {word_list}.")

    # Fluency feedback
    if fluency_score < 60:
        parts.append("Try to reduce pauses between words for smoother delivery.")
    elif fluency_score < 80:
        parts.append("Your pacing is mostly good, with a few noticeable hesitations.")

    # Clarity feedback
    if clarity_score < 60:
        parts.append(
            "Many words were difficult to recognize. "
            "Focus on enunciating each word clearly."
        )

    return " ".join(parts)
