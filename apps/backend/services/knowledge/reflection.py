"""Reflection trigger — delegates the actual Claude reasoning to Brain.

Knowledge owns no Claude logic of its own; this module is the
information-provider-facing entry point that nova.py and the tool
dispatcher call into.
"""

from services import brain


def run_reflection() -> str:
    return brain.run_reflection_job()


def should_run_reflection() -> bool:
    return brain.should_run_reflection()
