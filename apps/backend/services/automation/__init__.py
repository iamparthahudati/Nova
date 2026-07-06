"""Nova's Automation service — macOS app/URL launching, WhatsApp messaging,
and notifications via AppleScript.

Owns every "make the Mac do something" concern extracted from the composition root: the
COMMANDS registry, app/URL open resolution, WhatsApp launching via Contacts +
osascript, and Notification Center posts. A leaf dependency, same shape as
Calendar and Voice — it imports nothing from memory, services.brain,
services.calendar, services.planner, or services.voice, and nothing outside
this package should shell out to `osascript` for app launching, WhatsApp, or
notifications.

Callers (nova.py) consume only the names below.
"""

from .commands import COMMANDS, match_command, run_command, open_app
from .whatsapp import send_whatsapp_message
from .notifications import notify
from .pomodoro import start_pomodoro

__all__ = [
    "COMMANDS",
    "match_command",
    "run_command",
    "open_app",
    "send_whatsapp_message",
    "notify",
    "start_pomodoro",
]
