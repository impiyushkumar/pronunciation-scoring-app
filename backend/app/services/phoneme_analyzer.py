# -----------------------------------------------------------------------
# G2P phoneme analysis — converts transcribed words to expected phonemes
# -----------------------------------------------------------------------

import logging
import re
from typing import Dict, List

from app.services.transcription import WordInfo

logger = logging.getLogger("pronunciation-api.phoneme")

# Lazy-loaded singleton
_g2p = None


def _get_g2p():
    """Load g2p_en model once (singleton)."""
    global _g2p
    if _g2p is None:
        from g2p_en import G2p
        _g2p = G2p()
        logger.info("G2P model loaded successfully")
    return _g2p


# ARPAbet → IPA mapping for display (user-friendly)
ARPABET_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ",
    "AY": "aɪ", "B": "b", "CH": "tʃ", "D": "d", "DH": "ð",
    "EH": "ɛ", "ER": "ɝ", "EY": "eɪ", "F": "f", "G": "ɡ",
    "HH": "h", "IH": "ɪ", "IY": "i", "JH": "dʒ", "K": "k",
    "L": "l", "M": "m", "N": "n", "NG": "ŋ", "OW": "oʊ",
    "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v",
    "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}


def _clean_word(word: str) -> str:
    """Strip punctuation and normalize for G2P lookup."""
    return re.sub(r"[^\w']", "", word).strip().lower()


def _arpabet_to_string(phonemes: List[str]) -> str:
    """Convert a list of ARPAbet phonemes to a display string."""
    # Filter out spaces and empty strings
    cleaned = [p for p in phonemes if p.strip() and p != " "]
    return " ".join(cleaned)


def get_phonemes_for_words(words: List[WordInfo]) -> Dict[str, str]:
    """
    Convert each unique transcribed word to its ARPAbet phoneme string.

    Returns:
        Dict mapping lowercase word → ARPAbet phoneme string
        e.g. {"hello": "HH AH0 L OW1", "world": "W ER1 L D"}
    """
    g2p = _get_g2p()

    # Deduplicate words for efficiency
    unique_words = set()
    for w in words:
        cleaned = _clean_word(w.word)
        if cleaned:
            unique_words.add(cleaned)

    phoneme_map: Dict[str, str] = {}

    for word in unique_words:
        try:
            raw_phonemes = g2p(word)
            phoneme_str = _arpabet_to_string(raw_phonemes)
            if phoneme_str:
                phoneme_map[word] = phoneme_str
        except Exception as e:
            logger.warning(f"G2P failed for word '{word}': {e}")
            # Skip words that fail — don't crash the whole analysis
            continue

    logger.info(f"G2P converted {len(phoneme_map)} unique words")
    return phoneme_map
