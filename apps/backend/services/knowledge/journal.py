"""Journal helper — logs the entry, then asks Brain for a thoughtful reply."""

from memory import add_progress
from services import brain


def handle_journal(text: str) -> str:
    add_progress(text, area="journal")
    try:
        reply = brain.ask(
            f'I just journaled: "{text}". Please respond thoughtfully and supportively.',
            brain.history.get(),
        )
        brain.history.add_turn(text, reply)
        return reply
    except Exception:
        return "Journal entry saved."
