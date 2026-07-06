"""Task prioritization — picks which open tasks surface in a briefing or plan.

Currently a straight extraction of the ordering Memory already applies
(oldest-first via get_open_tasks' created_at ordering): take the first
`limit` tasks. Kept as its own function so briefing/daily/schedule share one
definition of "top tasks" instead of three copies of `tasks[:3]`, and so a
smarter ranking (due date, urgency) has a single place to land later.
"""


def prioritize_tasks(tasks: list[dict], limit: int = 3) -> list[dict]:
    return tasks[:limit]
