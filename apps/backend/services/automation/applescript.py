"""Centralized AppleScript execution via `osascript`."""

import subprocess
from typing import Optional


def run_applescript(
    script: str,
    *,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """Execute an AppleScript string via `osascript -e`."""
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        check=check,
    )
