"""macOS Calendar.app integration via AppleScript — event creation and retrieval."""

import re
import subprocess
from datetime import datetime
from typing import Optional, Tuple


def _as_date_block(var: str, dt: datetime) -> str:
    """Return AppleScript lines that set `var` to a specific datetime using numeric components."""
    return (
        f"  set {var} to current date\n"
        f"  set year of {var} to {dt.year}\n"
        f"  set month of {var} to {dt.month}\n"
        f"  set day of {var} to {dt.day}\n"
        f"  set hours of {var} to {dt.hour}\n"
        f"  set minutes of {var} to {dt.minute}\n"
        f"  set seconds of {var} to 0\n"
    )


def add_calendar_event(
    title: str, date_obj: datetime, time_tuple: Optional[Tuple[int, int]] = None
) -> bool:
    """Create an event in the default macOS Calendar via AppleScript."""
    hour, minute = time_tuple if time_tuple else (12, 0)
    start_dt = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "Calendar"\n'
        + _as_date_block("startDate", start_dt)
        + f"  set endDate to startDate + 3600\n"
        f"  set didAdd to false\n"
        f"  repeat with cal in calendars\n"
        f"    try\n"
        f"      tell cal\n"
        f'        make new event with properties {{summary:"{safe_title}", start date:startDate, end date:endDate}}\n'
        f"      end tell\n"
        f"      set didAdd to true\n"
        f"    end try\n"
        f"    if didAdd then exit repeat\n"
        f"  end repeat\n"
        f"  save\n"
        f"  return didAdd\n"
        f"end tell\n"
    )
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
        if result.returncode != 0:
            print(f"[error] AppleScript: {result.stderr.decode().strip()}")
            return False
        return True
    except Exception as exc:
        print(f"[error] add_calendar_event: {exc}")
        return False


def get_events(day: Optional[datetime] = None) -> list[dict]:
    """Return calendar events for a given local date via AppleScript."""
    if day is None:
        day = datetime.now()
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    script = (
        'tell application "Calendar"\n'
        + _as_date_block("startBound", day_start)
        + f"  set endBound to startBound + {23 * 3600 + 59 * 60 + 59}\n"
        f'  set output to ""\n'
        f"  repeat with cal in calendars\n"
        f"    try\n"
        f"      repeat with e in (every event of cal)\n"
        f"        set sd to start date of e\n"
        f"        if sd >= startBound and sd <= endBound then\n"
        f'          set output to output & (summary of e) & "|" & (time string of sd) & "\\n"\n'
        f"        end if\n"
        f"      end repeat\n"
        f"    end try\n"
        f"  end repeat\n"
        f"  return output\n"
        f"end tell\n"
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=15
        )
        events = []
        for line in result.stdout.strip().splitlines():
            if "|" in line:
                title_part, time_part = line.split("|", 1)
                # "4:00:00 PM" → "4:00 PM"  (narrow no-break space → regular)
                time_clean = re.sub(r":00(?=[\s ][AP]M)", "", time_part.strip())
                time_clean = time_clean.replace(" ", " ")
                events.append({"title": title_part.strip(), "time": time_clean})
        return events
    except Exception as exc:
        print(f"[error] get_events: {exc}")
        return []
