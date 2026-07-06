"""Voice service configuration.

Every tunable is overridable via environment variables (.env) so the
wake-word experience can be tuned without touching code. Defaults are
calibrated for a quiet-to-moderate room at 1–3 m from the microphone.
"""

import os

from dotenv import load_dotenv

from paths import REPO_ROOT

load_dotenv(REPO_ROOT / ".env")  # safe to call again if the composition root already loaded .env


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _env_words(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return [w.strip().lower() for w in raw.split(",") if w.strip()]


# ── Wake word matching ──────────────────────────────────────────────────────
# Keep in sync with ASSISTANT_NAME (identity.py); this package is
# import-isolated, so the wake word is configured here / via .env.
WAKE_WORD = _env_str("WAKE_WORD", "nova").lower()

# Aliases are Whisper's observed transcriptions of the wake phrase. "Nova"
# is a real English word, so Whisper hears it correctly at every volume;
# the one measured mishear is "hey nova" → "inova". Multi-word entries are
# matched as consecutive phrases. Watch the `Heard: "…"` log and add any
# new mishears here.
WAKE_WORD_ALIASES = _env_words("WAKE_WORD_ALIASES", ["hey nova", "inova"])

# Weak aliases: common English words Whisper produces for the wake word —
# they wake only when heard (near-)alone (see MAX_WEAK_UTTERANCE_WORDS).
# "Nova" transcribes cleanly, so none are needed by default. (The previous
# wake word "Rai" needed right/ride/ring here.)
WAKE_WEAK_ALIASES = _env_words("WAKE_WEAK_ALIASES", [])

# Fuzzy match: a word within this similarity of the wake word or an alias
# wakes the assistant (difflib ratio, 0..1). Catches unseen mishears
# ("inova" scores 0.89 vs "nova") without listing them. Note "novel" also
# scores 0.89 — raise toward 0.9 if that ever false-wakes in practice.
MIN_SIMILARITY = _env_float("MIN_SIMILARITY", 0.78)

# Wake utterances are short ("nova", "hey nova"). Longer utterances are
# conversation happening near the mic — never wake on them.
MAX_WAKE_UTTERANCE_WORDS = _env_int("MAX_WAKE_UTTERANCE_WORDS", 3)
MAX_WEAK_UTTERANCE_WORDS = _env_int("MAX_WEAK_UTTERANCE_WORDS", 2)

# ── Listening / speech gate ─────────────────────────────────────────────────
SAMPLE_RATE = 16_000  # Hz, mono — Whisper expects 16 kHz
HOP_SECONDS = _env_float("HOP_SECONDS", 1.0)  # listener advances by this much
WINDOW_SECONDS = _env_float("WINDOW_SECONDS", 2.0)  # 2 overlapping hops per check

# The speech gate decides whether a window is worth sending to Whisper.
# It compares the loudest RMS_FRAME_MS frame in the window (not the whole-
# window average, which dilutes a short word in 2 s of silence) against
# max(RMS_THRESHOLD, noise_floor * NOISE_MARGIN).
RMS_FRAME_MS = _env_int("RMS_FRAME_MS", 100)
RMS_THRESHOLD = _env_float("RMS_THRESHOLD", 0.003)  # absolute gate floor
NOISE_MARGIN = _env_float("NOISE_MARGIN", 2.5)  # gate = noise floor × this
NOISE_ALPHA = _env_float("NOISE_ALPHA", 0.05)  # noise-floor EMA weight
MAX_BACKLOG_SECONDS = _env_float("MAX_BACKLOG_SECONDS", 5.0)  # drop stale mic audio past this

# ── Gain normalization ──────────────────────────────────────────────────────
# Soft/distant speech is amplified to this peak before Whisper sees it, so
# a normal speaking voice at 2–3 m transcribes like close-mic speech.
GAIN_TARGET_PEAK = _env_float("GAIN_TARGET_PEAK", 0.9)
GAIN_MAX = _env_float("GAIN_MAX", 60.0)  # cap so noise isn't blown up

# ── Whisper ─────────────────────────────────────────────────────────────────
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"  # ~75 MB RAM on CPU

WHISPER_LANG = _env_str("WHISPER_LANG", "en")  # "en", "hi", "" = auto-detect
# Use multilingual Whisper when a non-English language is configured
WHISPER_MODEL = "base" if WHISPER_LANG not in ("en", "") else "base.en"

WAKE_BEAM_SIZE = _env_int("WAKE_BEAM_SIZE", 1)  # greedy: ~2× faster polling
COMMAND_BEAM_SIZE = _env_int("COMMAND_BEAM_SIZE", 5)
# Biases Whisper's decoder toward the wake phrase. "Nova" transcribes
# correctly even unbiased, but the bias also suppresses the "you"/"thank
# you" noise hallucinations, so keep it. Wake windows only, not commands.
WAKE_HOTWORDS = _env_str("WAKE_HOTWORDS", "Hey Nova")

# ── Command recording (endpointing) ─────────────────────────────────────────
# Commands record until the speaker stops instead of a fixed window: stop
# after SILENCE_DURATION of quiet once MIN_SPEECH_DURATION of speech was
# heard, capped at COMMAND_MAX_SECONDS. If no speech starts within
# COMMAND_WAIT_SECONDS, give up.
MIN_SPEECH_DURATION = _env_float("MIN_SPEECH_DURATION", 0.3)
SILENCE_DURATION = _env_float("SILENCE_DURATION", 1.0)
COMMAND_MAX_SECONDS = _env_float("COMMAND_MAX_SECONDS", 10.0)
COMMAND_WAIT_SECONDS = _env_float("COMMAND_WAIT_SECONDS", 5.0)
FOLLOWUP_TIMEOUT = _env_float("FOLLOWUP_TIMEOUT", 8.0)  # wake-free follow-up window

# ── TTS / cues ──────────────────────────────────────────────────────────────
TTS_ENGINE = _env_str("TTS_ENGINE", "say")  # "say" or "piper"
PIPER_BINARY = _env_str("PIPER_BINARY", "piper")
PIPER_MODEL = _env_str("PIPER_MODEL", "")
WAKE_CUE_SOUND = _env_str("WAKE_CUE_SOUND", "")  # path to .aiff/.mp3; empty = none
WAKE_RESPONSE = _env_str("WAKE_RESPONSE", "mm?")
