"""Natural-language date/time parsing for Calendar — no I/O, no AppleScript."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_MONTH_MAP = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


# DEBT(nova-ci-2): exceeds Handbook §3.1 max-complexity 12; needs decomposition.
def parse_date(text: str) -> Optional[datetime]:  # noqa: C901
    """Parse a natural-language date string into a datetime (midnight, local time)."""
    # Commas are separators, never meaning ("July 6, 2026" == "July 6 2026").
    t = text.lower().replace(",", " ").strip()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # ISO YYYY-MM-DD — the canonical format the tool schemas ask Claude for.
    # An explicit date is taken literally: no roll-to-next-year adjustment.
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})$", t)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    if t in ("today",):
        return today
    if t in ("tomorrow",):
        return today + timedelta(days=1)
    if t in ("yesterday",):
        return today - timedelta(days=1)

    # "next Monday", "next Friday"
    m = re.match(r"next (\w+)", t)
    if m and m.group(1) in _WEEKDAY_MAP:
        target = _WEEKDAY_MAP[m.group(1)]
        days = (target - today.weekday() + 7) % 7 or 7
        return today + timedelta(days=days)

    # bare weekday name ("Friday" → next Friday)
    if t in _WEEKDAY_MAP:
        target = _WEEKDAY_MAP[t]
        days = (target - today.weekday() + 7) % 7 or 7
        return today + timedelta(days=days)

    # "31st July", "10 July", "10th July 2026"
    m = re.match(r"(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)(?:\s+(\d{4}))?$", t)
    if m:
        day, month_name = int(m.group(1)), m.group(2)
        year = int(m.group(3)) if m.group(3) else today.year
        if month_name in _MONTH_MAP:
            try:
                result = today.replace(year=year, month=_MONTH_MAP[month_name], day=day)
                if result < today:
                    result = result.replace(year=year + 1)
                return result
            except ValueError:
                pass

    # "July 10", "July 10 2026"
    m = re.match(r"(\w+)\s+(\d{1,2})(?:\s+(\d{4}))?$", t)
    if m:
        month_name, day = m.group(1), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if month_name in _MONTH_MAP:
            try:
                result = today.replace(year=year, month=_MONTH_MAP[month_name], day=day)
                if result < today:
                    result = result.replace(year=year + 1)
                return result
            except ValueError:
                pass

    return None


def parse_relative(text: str) -> Optional[datetime]:
    """Parse a relative offset ('in 20 minutes', 'after 2 hours', 'in 3 days')
    into an absolute local datetime: now + offset, minute precision. Returns
    None for anything that isn't a bare relative-offset expression — absolute
    dates stay parse_date's job."""
    t = text.lower().replace(",", " ").strip()
    m = re.match(r"(?:in|after)?\s*(\d+|an?)\s+(minutes?|mins?|hours?|hrs?|days?|weeks?)$", t)
    if not m:
        return None
    count = 1 if m.group(1) in ("a", "an") else int(m.group(1))
    unit = m.group(2)
    if unit.startswith("min"):
        delta = timedelta(minutes=count)
    elif unit.startswith(("hour", "hr")):
        delta = timedelta(hours=count)
    elif unit.startswith("day"):
        delta = timedelta(days=count)
    else:
        delta = timedelta(weeks=count)
    return (datetime.now() + delta).replace(second=0, microsecond=0)


def parse_time(text: str) -> Optional[Tuple[int, int]]:
    """Parse a natural-language time string into (hour24, minute)."""
    t = text.lower().strip()
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", t)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2) or 0)
        if m.group(3) == "pm" and hour != 12:
            hour += 12
        elif m.group(3) == "am" and hour == 12:
            hour = 0
        return hour, minute
    m = re.match(r"(\d{1,2}):(\d{2})$", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None
