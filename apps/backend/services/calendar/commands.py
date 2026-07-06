"""Command-layer helpers for the calendar tool handlers — natural-language
input in, spoken confirmation string out. Built entirely on top of this
package's existing public functions (add_calendar_event, get_events,
parse_date, parse_time); those remain unchanged.
"""

from datetime import datetime
from typing import Optional

from .applescript import add_calendar_event, get_events
from .parsing import parse_date, parse_time


def create_event(title: str, date_str: str, time_str: Optional[str] = None) -> str:
    date_obj = parse_date(date_str)
    if not date_obj:
        return f"Sorry, I couldn't understand the date '{date_str}'."
    time_tuple = parse_time(time_str) if time_str else None
    ok = add_calendar_event(title, date_obj, time_tuple)
    if ok:
        date_label = date_obj.strftime("%B %d")
        time_label = ""
        if time_tuple:
            h, mn = time_tuple
            suffix = "AM" if h < 12 else "PM"
            h12 = h % 12 or 12
            time_label = f" at {h12}:{mn:02d} {suffix}"
        return f"Event added: {title} on {date_label}{time_label}."
    return "Sorry, I couldn't add the calendar event."


def describe_events(day_str: Optional[str] = None) -> str:
    day = parse_date(day_str) if day_str else datetime.now()
    if day is None:
        day = datetime.now()
    events = get_events(day)
    label = "today" if day.date() == datetime.now().date() else day.strftime("%A")
    if not events:
        return f"Nothing on your calendar {label}."
    event_strs = "; ".join(f"{e['title']} at {e['time']}" for e in events[:5])
    return f"On your calendar {label}: {event_strs}."
