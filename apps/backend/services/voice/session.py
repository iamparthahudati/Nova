import numpy as np
from faster_whisper import WhisperModel

from . import config
from .audio import (
    flush_input,
    normalize,
    peak_frame_rms,
    read_audio,
    record_endpointed,
    record_hop,
    rms,
    speech_gate,
    update_noise_floor,
)
from .transcription import transcribe
from .tts import speak
from .wake_word import play_wake_cue, wake_match

# Audio captured by wait_for_followup at the moment speech was detected.
# record_command() uses it as pre-roll so the first word of a follow-up is
# never clipped (the old fixed-window recorder lost up to 2 s of it).
_pending_audio: np.ndarray | None = None


def record_command(model: WhisperModel) -> str:
    """Record one utterance (until the speaker stops), transcribe it."""
    global _pending_audio
    print(f"Listening for command (up to {config.COMMAND_MAX_SECONDS:.0f}s)…")
    audio = record_endpointed(preroll=_pending_audio)
    _pending_audio = None
    print("Transcribing…")
    return transcribe(model, normalize(audio))


def poll_wake_word(model: WhisperModel, prev_hop: np.ndarray) -> tuple[bool, np.ndarray]:
    """One hop-step of the sliding-window wake-word listener.

    Reads one HOP_SECONDS chunk from the continuous stream and checks the
    2-hop window for the wake word. Returns (heard, new_prev_hop) —
    new_prev_hop becomes prev_hop on the next call. On detection, plays the
    wake cue and speaks the wake response as a side effect.
    """
    new_hop = record_hop()
    window = np.concatenate([prev_hop, new_hop])

    # Adaptive gate: skip Whisper unless some 100 ms frame rises clearly
    # above the ambient noise floor. Saves CPU and prevents faster-whisper
    # hallucinations on quiet audio ("you", "thank you.") from false-waking.
    update_noise_floor(window)
    level = peak_frame_rms(window)
    gate = speech_gate()
    print(f"[peak {level:.4f} | gate {gate:.4f}]", end="\r")
    if level < gate:
        return False, new_hop

    text = transcribe(model, normalize(window), wake=True)
    if not text:
        return False, new_hop
    print(f'[peak {level:.4f}] Heard: "{text}"')

    reason = wake_match(text)
    if reason:
        print(f"Wake word detected ({reason})")
        play_wake_cue()
        speak(config.WAKE_RESPONSE)
        return True, new_hop

    return False, new_hop


def wait_for_followup(model: WhisperModel) -> bool:
    """
    Listen for one follow-up utterance without requiring the wake word.

    Watches 100 ms frames for up to FOLLOWUP_TIMEOUT seconds. Returns True
    the moment speech rises above the adaptive gate (caller should then call
    record_command() to get the transcript — the detected audio is kept as
    pre-roll so nothing is clipped). Returns False once FOLLOWUP_TIMEOUT
    elapses with no speech, meaning the assistant should go back to wake-word-only
    listening.
    """
    global _pending_audio
    _pending_audio = None
    print(f"Listening for follow-up (up to {config.FOLLOWUP_TIMEOUT:.0f}s)…")

    flush_input()  # drop the assistant's own just-spoken reply picked up by the mic
    frame_seconds = config.RMS_FRAME_MS / 1000
    gate = speech_gate()
    recent: list[np.ndarray] = []
    max_recent = max(1, int(0.5 / frame_seconds))  # ~0.5 s pre-roll
    elapsed = 0.0

    while elapsed < config.FOLLOWUP_TIMEOUT:
        frame = read_audio(frame_seconds)
        elapsed += frame_seconds
        recent.append(frame)
        recent = recent[-max_recent:]

        if rms(frame) >= gate:
            print("Follow-up speech detected.")
            _pending_audio = np.concatenate(recent)
            return True

    return False
