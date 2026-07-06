"""RSS feed headline lookups."""

import os
import urllib.request
import xml.etree.ElementTree as ET

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


RSS_FEEDS = _env("RSS_FEEDS")  # comma-separated
_USER_AGENT = f"{os.environ.get('ASSISTANT_NAME', 'Nova')}/1.0"


def get_rss_updates(feed_urls: list[str] | None = None, limit: int = 3) -> str:
    """Return recent headlines from configured RSS feeds."""
    urls = feed_urls or [u.strip() for u in RSS_FEEDS.split(",") if u.strip()]
    if not urls:
        return "No RSS feeds configured. Add NOVA_RSS_FEEDS to your .env file."
    items = []
    for url in urls[:3]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
            root = ET.fromstring(raw)
            ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
            for item in (root.findall(f".//{ns}item") or root.findall(".//item"))[:limit]:
                title_el = item.find(f"{ns}title") or item.find("title")
                if title_el is not None and title_el.text:
                    items.append(title_el.text.strip())
        except Exception as exc:
            print(f"[error] get_rss_updates({url}): {exc}")
    if not items:
        return "No RSS updates available right now."
    return "Latest headlines: " + "; ".join(items[:limit]) + "."
