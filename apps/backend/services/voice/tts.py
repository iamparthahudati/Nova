import subprocess

from . import config


def speak(text: str) -> None:
    """Speak text using the configured TTS engine (TTS_ENGINE=say or piper).

    Piper setup: install piper, set PIPER_BINARY and PIPER_MODEL in .env.
    Piper reads text from stdin and writes a WAV to stdout; afplay plays it.
    Falls back to 'say' on any error.
    """
    if config.TTS_ENGINE == "piper" and config.PIPER_BINARY and config.PIPER_MODEL:
        try:
            result = subprocess.run(
                [
                    config.PIPER_BINARY,
                    "--model",
                    config.PIPER_MODEL,
                    "--output-file",
                    "/dev/stdout",
                    "--quiet",
                ],
                input=text.encode(),
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                subprocess.run(["afplay", "-"], input=result.stdout, timeout=30)
                return
        except Exception as exc:
            print(f"[warn] piper TTS failed: {exc}; falling back to 'say'")
    subprocess.run(["say", text])
