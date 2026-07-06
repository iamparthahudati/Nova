"""Rolling conversation history for the current wake-word session."""

MAX_HISTORY_TURNS = 4  # keep last 4 user-assistant pairs = 8 messages

_session_history: list[dict] = []


def trim(history: list[dict], max_turns: int = MAX_HISTORY_TURNS) -> list[dict]:
    """Return the last max_turns user-assistant pairs from history."""
    max_msgs = max_turns * 2
    return history[-max_msgs:] if len(history) > max_msgs else list(history)


def get() -> list[dict]:
    """Return the trimmed current session history."""
    return trim(_session_history)


def add_turn(user_text: str, assistant_text: str) -> None:
    _session_history.append({"role": "user", "content": user_text})
    _session_history.append({"role": "assistant", "content": assistant_text})


def clear() -> None:
    _session_history.clear()
