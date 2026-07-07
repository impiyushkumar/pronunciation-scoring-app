# -----------------------------------------------------------------------
# LLM Analyzer — Gemini Flash for error classification + feedback
# -----------------------------------------------------------------------

import json
import logging
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services.transcription import WordInfo

logger = logging.getLogger("pronunciation-api.llm")

# Lazy-loaded client
_client = None


def _get_client():
    """Initialize the Gemini client once (singleton)."""
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — LLM analysis disabled")
            return None
        from google import genai
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini client initialized")
    return _client


# ------- Prompt template -------

ANALYSIS_PROMPT = """You are an expert English pronunciation coach analyzing a speech-to-text transcription result.

## Input Data
**Full transcript:** {transcript}

**Words with confidence scores and expected phonemes:**
{word_table}

## Your Task
Analyze the transcript and classify pronunciation issues for words with low confidence (below 0.70). For each flagged word, determine the most likely error type:

- **mispronunciation**: The word was spoken but sounds wrong (wrong vowel/consonant sounds, wrong stress pattern)
- **unclear**: The word was barely intelligible (mumbled, too fast, swallowed syllables)  
- **omission**: A word that should be present was skipped or replaced with silence/filler

Also provide:
1. An overall assessment paragraph (2-3 sentences)
2. 3-5 specific, actionable pronunciation tips based on the errors you see
3. For flagged words, explain what the speaker likely did wrong phonetically

## Output Format
Respond ONLY with valid JSON in this exact structure — no markdown, no code fences, no extra text:
{{
  "word_classifications": {{
    "<word_at_position>": {{
      "error_type": "mispronunciation" | "unclear" | "omission",
      "explanation": "brief phonetic explanation"
    }}
  }},
  "overall_feedback": "2-3 sentence overall assessment",
  "tips": ["tip 1", "tip 2", "tip 3"]
}}

The keys in word_classifications should be in the format "word@start_time" (e.g., "phone@1.10") to identify specific word instances.
Only include words that actually have pronunciation issues (confidence < 0.70).
If all words have good confidence, return empty word_classifications and positive feedback.
"""


def _build_word_table(words: List[WordInfo], phoneme_map: Dict[str, str]) -> str:
    """Build a formatted table of words for the LLM prompt."""
    import re
    lines = []
    for w in words:
        cleaned = re.sub(r"[^\w']", "", w.word).strip().lower()
        phonemes = phoneme_map.get(cleaned, "N/A")
        flag = " ⚠️" if w.probability < 0.70 else ""
        lines.append(
            f"| {w.word:<20} | {w.start:>6.2f}s | {w.end:>6.2f}s | "
            f"{w.probability:>5.1%} | {phonemes:<30} |{flag}"
        )
    header = f"| {'Word':<20} | {'Start':>6} | {'End':>6} | {'Conf':>5} | {'Expected Phonemes':<30} |"
    separator = f"|{'-'*22}|{'-'*8}|{'-'*8}|{'-'*7}|{'-'*32}|"
    return "\n".join([header, separator] + lines)


def analyze_with_llm(
    words: List[WordInfo],
    transcript: str,
    phoneme_map: Dict[str, str],
) -> Optional[Dict]:
    """
    Send transcript + confidence data to Gemini Flash for error classification.
    
    Returns parsed JSON dict with:
      - word_classifications: dict of "word@time" → {error_type, explanation}
      - overall_feedback: str
      - tips: list[str]
    
    Returns None if LLM is unavailable or fails (caller falls back to heuristics).
    """
    client = _get_client()
    if client is None:
        return None

    # Build prompt
    word_table = _build_word_table(words, phoneme_map)
    prompt = ANALYSIS_PROMPT.format(
        transcript=transcript,
        word_table=word_table,
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)

        result = json.loads(raw_text)

        # Validate expected structure
        if not isinstance(result, dict):
            logger.warning("LLM returned non-dict response")
            return None

        logger.info(
            f"LLM analysis complete: "
            f"{len(result.get('word_classifications', {}))} words classified, "
            f"{len(result.get('tips', []))} tips"
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")
        return None


def apply_llm_classifications(
    words: List[WordInfo],
    llm_result: Dict,
) -> Tuple[Dict[str, Dict], str, List[str]]:
    """
    Extract LLM classifications and map them back to words by position.
    
    Returns:
      - word_errors: dict mapping "word@start" → {error_type, explanation}
      - feedback: overall feedback string
      - tips: list of actionable tips
    """
    word_classifications = llm_result.get("word_classifications", {})
    feedback = llm_result.get("overall_feedback", "")
    tips = llm_result.get("tips", [])

    # Build lookup by word@start
    word_errors: Dict[str, Dict] = {}
    for key, value in word_classifications.items():
        if isinstance(value, dict) and "error_type" in value:
            error_type = value["error_type"]
            if error_type in ("mispronunciation", "unclear", "omission"):
                word_errors[key] = value

    # Format feedback with tips
    if tips:
        tips_text = " ".join(f"• {tip}" for tip in tips[:5])
        feedback = f"{feedback}\n\nTips for improvement:\n{tips_text}"

    return word_errors, feedback, tips
