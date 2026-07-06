"""GitHub notifications lookup."""

import json
import os
import urllib.request

_WARNED_LEGACY_ENV: set[str] = set()


def _env(name: str, default: str = "") -> str:
    """Read NOVA_<name> first, then legacy RAI_<name> with a warning."""
    nova_key = f"NOVA_{name}"
    legacy_key = f"RAI_{name}"
    if nova_key in os.environ:
        return os.environ[nova_key]
    if legacy_key in os.environ:
        if legacy_key not in _WARNED_LEGACY_ENV:
            print(f"[deprecated] {legacy_key} is deprecated; use {nova_key} instead.")
            _WARNED_LEGACY_ENV.add(legacy_key)
        return os.environ[legacy_key]
    return default


GITHUB_TOKEN = _env("GITHUB_TOKEN")


def get_github_notifications(limit: int = 5) -> str:
    """Return a summary of unread GitHub notifications."""
    if not GITHUB_TOKEN:
        return "GitHub token not configured. Add NOVA_GITHUB_TOKEN to your .env file."
    url = f"https://api.github.com/notifications?per_page={limit}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            notifications = json.loads(resp.read())
        if not notifications:
            return "No new GitHub notifications."
        count = len(notifications)
        parts = []
        for n in notifications[:limit]:
            repo = n["repository"]["full_name"]
            subject = n["subject"]["title"]
            ntype = n["subject"]["type"]
            parts.append(f"{ntype} in {repo}: {subject}")
        summary = "; ".join(parts)
        return f"{count} GitHub notification{'s' if count != 1 else ''}: {summary}."
    except Exception as exc:
        print(f"[error] get_github_notifications: {exc}")
        return "Sorry, I couldn't fetch GitHub notifications right now."
