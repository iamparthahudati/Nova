"""Assistant identity — the single source for the name "Nova".

Who reads this file:
  - Root modules (nova.py, dashboard.py, conversation_memory.py) and Brain
    import it directly (Brain already imports root-level packages: memory).
  - Import-isolated services (voice, automation, knowledge) may not import
    anything outside their own package, so they read the same ASSISTANT_NAME
    environment variable themselves with the same default. `.env` is the one
    shared override point; this module is the one code home for the default.

Wake phrases are Voice configuration, not identity: see WAKE_WORD /
WAKE_WORD_ALIASES in services/voice/config.py (env-overridable). Keep them
in sync with ASSISTANT_NAME when renaming the assistant.

History: the assistant was called "Rai" through Phases 0–7. Data-bearing
names now use Nova storage paths (`nova.db`, `nova_lancedb/`) and keep
backward compatibility via automatic migration from legacy Rai paths.
"""

import os

from dotenv import load_dotenv
from paths import REPO_ROOT

load_dotenv(REPO_ROOT / ".env")  # safe to call again if the composition root already did

ASSISTANT_NAME = os.environ.get("ASSISTANT_NAME", "Nova")

# Persona name for the assistant's voice (display label, e.g. in the
# dashboard) — not a macOS `say` voice; the TTS engine is services/voice/tts.
VOICE_NAME = os.environ.get("VOICE_NAME", ASSISTANT_NAME)
