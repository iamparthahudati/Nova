"""Nova's Brain service — Claude API calls, prompt building, conversation
history, tool routing, and tool execution.

Owns everything that talks to Claude. It has no knowledge of WhatsApp,
Calendar, weather, or any other concrete action: callers pass in `handlers`
(a dict mapping tool name -> a function that takes the tool's input dict and
returns a spoken-response string) and Brain only decides which one to call.
"""

from . import history
from .client import ask, route
from .config import (
    ANTHROPIC_API_URL, CLAUDE_API_KEY, CLAUDE_MODEL, REPLY_LANGUAGE,
    check_api_config,
)
from .context_engine import build_system_prompt, set_calendar_source
from .extraction import run_entity_extraction
from .reflection import run_reflection_job, should_run_reflection
from .tools import ASSISTANT_TOOLS, execute as execute_tool

__all__ = [
    "history",
    "ask",
    "route",
    "ANTHROPIC_API_URL",
    "CLAUDE_API_KEY",
    "CLAUDE_MODEL",
    "REPLY_LANGUAGE",
    "check_api_config",
    "build_system_prompt",
    "set_calendar_source",
    "run_entity_extraction",
    "run_reflection_job",
    "should_run_reflection",
    "ASSISTANT_TOOLS",
    "execute_tool",
]
