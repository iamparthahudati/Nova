"""Wake-word decision logic.

Whisper doesn't always transcribe the wake phrase literally — it snaps
unfamiliar sounds to nearby English words ("hey nova" → "inova"; the old
wake word "Rai" became "right"/"ray"/"rye"). Exact matching against one
spelling therefore misses genuine wakes. Instead:

1. Strong aliases — observed transcriptions that rarely occur as
   standalone utterances — wake directly (multi-word entries match as
   consecutive phrases).
2. Weak aliases — common English words — wake only when heard
   (near-)alone, so they never fire mid-sentence.
3. Fuzzy similarity against the wake word and strong aliases catches
   mishears nobody listed.
4. An utterance-length gate rejects sentences: people talking near the mic
   don't wake the assistant just because a wake-like word appeared
   mid-sentence.
"""

import re
import subprocess
from difflib import SequenceMatcher

from . import config

_WORDS = re.compile(r"[a-z']+")


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def wake_match(text: str) -> str | None:
    """Return a short reason string if text should wake the assistant, else None."""
    words = _WORDS.findall(text.lower())
    if not words:
        return None

    if len(words) <= config.MAX_WEAK_UTTERANCE_WORDS:
        for word in words:
            if word in config.WAKE_WEAK_ALIASES:
                return f"weak alias '{word}'"

    if len(words) > config.MAX_WAKE_UTTERANCE_WORDS:
        return None

    padded = f" {' '.join(words)} "
    single = [config.WAKE_WORD]
    for alias in config.WAKE_WORD_ALIASES:
        if " " in alias:  # phrase alias, e.g. "hey nova"
            if f" {alias} " in padded:
                return f"phrase '{alias}'"
        else:
            single.append(alias)

    for word in words:
        if word in single:
            return f"alias '{word}'"
        best_target = max(single, key=lambda t: _similarity(word, t))
        best = _similarity(word, best_target)
        if best >= config.MIN_SIMILARITY:
            return f"'{word}' ≈ '{best_target}' ({best:.2f})"
    return None


def is_wake_word(text: str) -> bool:
    return wake_match(text) is not None


def play_wake_cue() -> None:
    if config.WAKE_CUE_SOUND:
        subprocess.run(["afplay", config.WAKE_CUE_SOUND], check=False)
