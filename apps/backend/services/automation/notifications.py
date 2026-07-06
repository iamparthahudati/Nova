"""macOS Notification Center posts via AppleScript."""

import os

from .applescript import run_applescript

# This package is import-isolated, so the display name comes from the same
# ASSISTANT_NAME env var identity.py reads (same default).
ASSISTANT_NAME = os.environ.get("ASSISTANT_NAME", "Nova")


def notify(message: str, title: str = ASSISTANT_NAME) -> None:
    """Post a macOS Notification Center alert."""
    run_applescript(
        f'display notification "{message}" with title "{title}"',
        capture_output=False,
        text=False,
    )
