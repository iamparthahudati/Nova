"""Recent-activity provider — the ambient "what's going on" block from Phase 1
(recent progress, recent money entries, product pipeline), unchanged in
content and rendering. Items carry a `group` meta so the section renders as
the same three titled sub-blocks it always has.
"""

from memory import get_products, get_recent_money, get_recent_progress

from ...config import ACTIVITY_CONTEXT_TOKEN_BUDGET
from ..base import ContextItem, ContextProvider, ContextRequest


class RecentActivityProvider(ContextProvider):
    name = "recent_activity"
    title = "Recent Context"
    budget = ACTIVITY_CONTEXT_TOKEN_BUDGET

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        items: list[ContextItem] = []

        for p in get_recent_progress(5):
            items.append(ContextItem(
                text=p["note"],
                meta={"group": "Recent progress"},
            ))

        for m in get_recent_money(5):
            line = f"{m['type']} {m['amount']}" + (
                f" ({m['note']})" if m.get("note") else ""
            )
            items.append(ContextItem(text=line, meta={"group": "Recent money entries"}))

        for p in get_products():
            line = (
                f"{p['name']} [{p['status']}]"
                + (f" store:{p['store']}" if p.get("store") else "")
                + (f" price:{p['price']}" if p.get("price") is not None else "")
                + f" sales:{p['sold_count']}"
            )
            items.append(ContextItem(text=line, meta={"group": "Products"}))

        return items
