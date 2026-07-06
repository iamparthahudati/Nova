"""Microphone capture and speech gating.

One continuous InputStream feeds a frame queue; readers assemble hops,
windows, or endpointed recordings from it. Because capture never stops,
audio arriving while Whisper is busy transcribing is buffered instead of
lost — the old start/stop `sd.rec` approach went deaf during every
transcription, which is one reason wake words were missed.

Callers that begin a fresh listening session must flush the queue first
(new_listener_state() and record_endpointed() do) so the assistant's own TTS output,
picked up by the mic while speaking, is never interpreted as user speech.
"""

import queue

import numpy as np
import sounddevice as sd

from . import config

_FRAME_SAMPLES = int(config.SAMPLE_RATE * config.RMS_FRAME_MS / 1000)
_FRAME_SECONDS = config.RMS_FRAME_MS / 1000

_stream: sd.InputStream | None = None
_frames: "queue.Queue[np.ndarray]" = queue.Queue()
_noise_floor: float | None = None


def _on_audio(indata, frames, time_info, status) -> None:  # noqa: ARG001
    _frames.put(indata[:, 0].copy())


def _ensure_stream() -> None:
    global _stream
    if _stream is None:
        _stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=_FRAME_SAMPLES,
            callback=_on_audio,
        )
        _stream.start()


def flush_input() -> None:
    """Drop all buffered mic audio (e.g. the assistant's own TTS echo)."""
    while True:
        try:
            _frames.get_nowait()
        except queue.Empty:
            return


def read_audio(seconds: float) -> np.ndarray:
    """Read ~seconds of audio from the continuous stream (blocking)."""
    _ensure_stream()
    needed = int(seconds * config.SAMPLE_RATE)
    chunks: list[np.ndarray] = []
    got = 0
    while got < needed:
        frame = _frames.get()
        chunks.append(frame)
        got += len(frame)
    return np.concatenate(chunks)


def record_audio(seconds: float, sample_rate: int = config.SAMPLE_RATE) -> np.ndarray:
    """Record mono audio from the default microphone (compat wrapper)."""
    assert sample_rate == config.SAMPLE_RATE, "stream runs at config.SAMPLE_RATE"
    return read_audio(seconds)


def record_hop() -> np.ndarray:
    """Read one HOP_SECONDS chunk, dropping stale backlog beyond the cap."""
    _ensure_stream()
    if _frames.qsize() * _FRAME_SECONDS > config.MAX_BACKLOG_SECONDS:
        flush_input()
    return read_audio(config.HOP_SECONDS)


def new_listener_state() -> np.ndarray:
    """A zeroed hop buffer — the initial (or reset) sliding-window state.

    Also starts the mic stream and flushes any audio buffered while the assistant was
    busy (processing a command, speaking a reply), so a fresh listening
    session never begins with stale or self-generated audio.
    """
    _ensure_stream()
    flush_input()
    hop_frames = int(config.HOP_SECONDS * config.SAMPLE_RATE)
    return np.zeros(hop_frames, dtype="float32")


# ── Levels, gate, and gain ──────────────────────────────────────────────────


def rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk**2)))


def _frame_rms(chunk: np.ndarray) -> np.ndarray:
    n = len(chunk) - len(chunk) % _FRAME_SAMPLES
    if n == 0:
        return np.array([rms(chunk)])
    frames = chunk[:n].reshape(-1, _FRAME_SAMPLES)
    return np.sqrt((frames**2).mean(axis=1))


def peak_frame_rms(chunk: np.ndarray) -> float:
    """Loudest RMS_FRAME_MS frame — detects a short word inside a mostly
    silent window, which whole-window mean RMS dilutes below the gate."""
    return float(_frame_rms(chunk).max())


def update_noise_floor(chunk: np.ndarray) -> None:
    """Track ambient level as an EMA of the window's median frame RMS.

    The median is robust to a short word inside the window, so speech
    doesn't drag the floor up; a genuinely noisy room does.
    """
    global _noise_floor
    level = float(np.median(_frame_rms(chunk)))
    if _noise_floor is None:
        _noise_floor = level
    else:
        _noise_floor += config.NOISE_ALPHA * (level - _noise_floor)


def speech_gate() -> float:
    """Current speech/silence threshold for peak-frame RMS."""
    if _noise_floor is None:
        return config.RMS_THRESHOLD
    return max(config.RMS_THRESHOLD, _noise_floor * config.NOISE_MARGIN)


def normalize(chunk: np.ndarray) -> np.ndarray:
    """Scale audio to GAIN_TARGET_PEAK so soft/distant speech transcribes
    like close-mic speech. Gain is capped so near-silence isn't amplified
    into Whisper hallucination fodder."""
    peak = float(np.abs(chunk).max())
    if peak < 1e-4:
        return chunk
    gain = min(config.GAIN_TARGET_PEAK / peak, config.GAIN_MAX)
    return chunk * gain


# ── Endpointed recording ────────────────────────────────────────────────────


def record_endpointed(preroll: np.ndarray | None = None) -> np.ndarray:
    """Record until the speaker stops talking.

    Stops after SILENCE_DURATION of quiet once MIN_SPEECH_DURATION of speech
    was heard, capped at COMMAND_MAX_SECONDS. Gives up after
    COMMAND_WAIT_SECONDS if speech never starts.

    preroll: already-captured audio containing the start of the utterance
    (from wait_for_followup); when given, the input queue is NOT flushed so
    no speech between detection and this call is lost.
    """
    _ensure_stream()
    if preroll is None:
        flush_input()
        chunks: list[np.ndarray] = []
        speech = 0.0
    else:
        chunks = [preroll]
        speech = config.MIN_SPEECH_DURATION  # detection already heard speech

    gate = speech_gate()
    silence = 0.0
    recorded = 0.0
    while recorded < config.COMMAND_MAX_SECONDS:
        frame = read_audio(_FRAME_SECONDS)
        chunks.append(frame)
        recorded += _FRAME_SECONDS

        if rms(frame) >= gate:
            speech += _FRAME_SECONDS
            silence = 0.0
        elif speech >= config.MIN_SPEECH_DURATION:
            silence += _FRAME_SECONDS
            if silence >= config.SILENCE_DURATION:
                break
        elif recorded >= config.COMMAND_WAIT_SECONDS and speech == 0.0:
            break  # nobody spoke

    return np.concatenate(chunks)
