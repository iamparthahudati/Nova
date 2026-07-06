"""Planner scheduling config — when the daily briefing/wrap-up fire."""

# Morning briefing fires once when local time first reaches this (24h "HH:MM").
BRIEFING_TIME = "09:00"

# Evening wrap-up fires once when local time first reaches this. Set to None to disable.
EVENING_WRAPUP_TIME = "21:00"
