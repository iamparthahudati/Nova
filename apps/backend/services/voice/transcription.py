import numpy as np
from faster_whisper import WhisperModel

from . import config


def load_model() -> WhisperModel:
    return WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )


def transcribe(model: WhisperModel, audio: np.ndarray, *, wake: bool = False) -> str:
    """Transcribe audio locally with faster-whisper; return lowercase text.

    wake=True tunes decoding for wake-word polling: greedy decoding for
    speed, and hotword biasing so Whisper stops snapping the non-English
    wake word to unrelated English words (e.g. "Rai" → "right" for the old wake word).
    """
    lang = config.WHISPER_LANG if config.WHISPER_LANG else None
    segments, _ = model.transcribe(
        audio,
        language=lang,
        beam_size=config.WAKE_BEAM_SIZE if wake else config.COMMAND_BEAM_SIZE,
        hotwords=(config.WAKE_HOTWORDS or None) if wake else None,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text for segment in segments).strip().lower()
