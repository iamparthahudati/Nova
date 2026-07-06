"""Weekly profile reflection — feeds recent activity logs to Claude and stores observations."""

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone

from memory import (
    get_recent_open_tasks, get_done_tasks_since, get_money_since, get_progress_since,
    get_profile_observations, get_last_profile_update, replace_profile_observations,
)

from .config import ANTHROPIC_API_URL, CLAUDE_API_KEY, CLAUDE_MODEL


def should_run_reflection() -> bool:
    """Return True if no reflection has run yet or last one was 7+ days ago."""
    last_iso = get_last_profile_update()
    if not last_iso:
        return True
    last = datetime.fromisoformat(last_iso)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last).days >= 7


def run_reflection_job() -> str:
    """Feed recent logs to Claude; write back profile observations (clears old ones)."""
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    open_tasks = get_recent_open_tasks(20)
    done_tasks = get_done_tasks_since(cutoff, 20)
    money_rows = get_money_since(cutoff, 30)
    prog_rows = get_progress_since(cutoff, 20)

    existing = get_profile_observations()
    existing_text = "\n".join(
        f"- [{o['category']}] {o['observation']} (confidence {o['confidence']:.1f})"
        for o in existing
    ) or "None yet."

    open_text  = "\n".join(
        f"- {r['text']}" + (f" (due {r['due']})" if r['due'] else "")
        for r in open_tasks
    ) or "None"
    done_text  = "\n".join(f"- {r['text']}" for r in done_tasks) or "None"
    money_text = "\n".join(
        f"- {r['type']} {r['amount']}" + (f" ({r['note']})" if r['note'] else "")
        for r in money_rows
    ) or "None"
    prog_text  = "\n".join(f"- {r['note']}" for r in prog_rows) or "None"

    prompt = (
        "You are analyzing behavioral data to build a profile for a personal assistant.\n\n"
        f"Last 30 days:\n\n"
        f"Open tasks:\n{open_text}\n\n"
        f"Completed tasks:\n{done_text}\n\n"
        f"Money log:\n{money_text}\n\n"
        f"Progress notes:\n{prog_text}\n\n"
        f"Current profile observations (carry forward if still true, drop if outdated):\n{existing_text}\n\n"
        "Extract 3–6 concise, specific observations about the user's patterns and tendencies. "
        "Base them only on the data above — do not speculate.\n"
        'Respond with JSON only: {"observations": [{"text": "...", "category": "...", "confidence": 0.0}]}\n'
        "Valid categories: habits, work, finances, productivity, health, social"
    )

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 512,
        "system": "You extract behavioral patterns from personal data logs. Respond with JSON only.",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
        raw = body["content"][0]["text"].strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        observations = data.get("observations", [])
        replace_profile_observations(observations)
        count = len([o for o in observations if o.get("text", "").strip()])
        return f"Reflection complete. {count} profile observation{'s' if count != 1 else ''} updated."
    except Exception as exc:
        print(f"[error] reflection job: {exc}")
        return "Reflection job failed — I'll try again next week."
