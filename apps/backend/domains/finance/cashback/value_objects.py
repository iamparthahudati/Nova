"""Cashback value objects and constants."""

from __future__ import annotations

DEFAULT_QUALIFYING_KINDS = frozenset({"expense"})


class MultiplierScale:
    """Multiplier stored as integer hundredths — 200 means 2.00x."""

    SCALE = 100
