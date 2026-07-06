"""Recent-conversation provider — the messages channel (Milestone 2.8).

Dialogue reaches Claude as a threaded `messages` array, never flattened into
the system string (duplicating it there would pay for every turn twice and
break tool-use threading). So this provider feeds the engine's messages
channel rather than a titled section, and its whole judgment is the trimming
policy — which moves here from the call sites so the Context Engine owns
every context decision, including "how much dialogue".

history.py remains the session-state owner (add_turn/clear); this provider
only shapes what one turn sends.
"""

from ...history import trim
from ..base import ContextRequest, MessagesProvider


class RecentConversationProvider(MessagesProvider):
    name = "recent_conversation"

    def collect(self, request: ContextRequest) -> list[dict]:
        return trim(list(request.history))
