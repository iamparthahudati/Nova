"""Nova's Voice service — microphone, wake word, Whisper STT, TTS.

Owns every raw audio operation in Nova. It has no knowledge of Brain,
Memory, or any other service: callers pass it nothing but plain data
(model handles, transcript strings) and get plain data back. Nothing in
this package imports from outside it.
"""

from .audio import new_listener_state
from .session import poll_wake_word, record_command, wait_for_followup
from .transcription import load_model
from .tts import speak

__all__ = [
    "load_model",
    "speak",
    "new_listener_state",
    "poll_wake_word",
    "record_command",
    "wait_for_followup",
]
