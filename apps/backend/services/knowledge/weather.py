"""Weather lookups via wttr.in (no auth required)."""

import json
import os
import urllib.parse
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


HOME_LOCATION = _env("LOCATION")  # e.g. "Mumbai"; empty = wttr.in auto-detect
_USER_AGENT = f"{os.environ.get('ASSISTANT_NAME', 'Nova')}/1.0"


def get_weather(location: str = "") -> str:
    """Return a short weather summary using wttr.in (no auth required)."""
    loc = location or HOME_LOCATION or ""
    path = urllib.parse.quote(loc) if loc else ""
    url = f"https://wttr.in/{path}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        feels_c = current["FeelsLikeC"]
        desc = current["weatherDesc"][0]["value"]
        area_list = data.get("nearest_area", [{}])[0].get("areaName", [{}])
        area = area_list[0].get("value", "") if area_list else ""
        area_str = f" in {area}" if area else ""
        return f"Right now{area_str}: {desc}, {temp_c}°C, feels like {feels_c}°C."
    except Exception as exc:
        print(f"[error] get_weather: {exc}")
        return "Sorry, I couldn't fetch the weather right now."
