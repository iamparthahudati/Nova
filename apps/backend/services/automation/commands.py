"""macOS app/URL launching — the COMMANDS registry and its resolvers."""

import subprocess
from typing import List, Optional, Tuple

# Spoken phrase (substring) -> macOS command list passed to subprocess.run().
COMMANDS = {
    # Apps
    "chrome": ["open", "-a", "Google Chrome"],
    "vs code": ["open", "-a", "Visual Studio Code"],
    "vscode": ["open", "-a", "Visual Studio Code"],
    "code": ["open", "-a", "Visual Studio Code"],
    # WhatsApp.app on this Mac has a hidden U+200E mark before its name, so
    # `open -a WhatsApp` can't resolve it by name — open the bundle path instead.
    "whatsapp": ["open", "/Applications/‎WhatsApp.app"],
    "what's up": [
        "open",
        "/Applications/‎WhatsApp.app",
    ],  # base.en mishears "WhatsApp" phonetically
    "whats up": ["open", "/Applications/‎WhatsApp.app"],
    "spotify": ["open", "-a", "Spotify"],
    "terminal": ["open", "-a", "Terminal"],
    "finder": ["open", "-a", "Finder"],
    "notes": ["open", "-a", "Notes"],
    # Websites
    "amazon": ["open", "https://www.amazon.com"],
    "youtube": ["open", "https://www.youtube.com"],
    "gmail": ["open", "https://mail.google.com"],
    "github": ["open", "https://github.com"],
}


def match_command(transcript: str) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Find the first COMMANDS entry whose phrase appears in the transcript.

    Longer phrases are checked first so "vs code" wins over "code".
    """
    for phrase in sorted(COMMANDS, key=len, reverse=True):
        if phrase in transcript:
            return phrase, COMMANDS[phrase]
    return None, None


def run_command(cmd: list[str]) -> None:
    """Run a macOS open command."""
    subprocess.run(cmd, check=True)


def open_app(target: str) -> str:
    """Resolve a spoken/typed app or URL target and open it."""
    for phrase in sorted(COMMANDS, key=len, reverse=True):
        if phrase in target or target in phrase:
            run_command(COMMANDS[phrase])
            return f"Opening {target}."
    res = subprocess.run(["open", "-a", target], capture_output=True)
    if res.returncode == 0:
        return f"Opening {target}."
    res = subprocess.run(["open", "-a", target.title()], capture_output=True)
    if res.returncode == 0:
        return f"Opening {target}."
    if target.startswith("http"):
        subprocess.run(["open", target])
        return f"Opening {target}."
    return f"I couldn't find {target}."
