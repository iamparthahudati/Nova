"""Claude API configuration — endpoint, model, key, and reply-language preference."""

import os
import sys

from dotenv import load_dotenv

from paths import REPO_ROOT

load_dotenv(REPO_ROOT / ".env")  # safe to call again if the composition root already loaded .env


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


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_KEY = _env("CLAUDE_API_KEY")
CLAUDE_MODEL = _env("MODEL", "claude-haiku-4-5-20251001")
REPLY_LANGUAGE = os.environ.get("REPLY_LANGUAGE", "")  # e.g. "Hinglish" or "Hindi"


# ── Semantic memory (Milestone 2.3) ───────────────────────────────────────────
# Brain's knobs for consuming memory.recall() / memory.record_access(). These
# live here — not in memory/ranking.py — because they are Brain's *consumption*
# policy (how much context to pull, how tight the relevance gate, how much of a
# turn's token budget the memory block may claim), which is a different concern
# from Memory's internal *ranking* policy. Brain never imports RankingConfig.


def _env_bool(name: str, default: bool) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except (TypeError, ValueError):
        return default


# Master switch: if recall is unavailable (e.g. embedding model not yet
# downloaded on a fresh offline machine) Brain degrades to Phase-1 behaviour.
SEMANTIC_MEMORY_ENABLED = _env_bool("SEMANTIC_MEMORY", True)

# How many candidates to ask recall() for. Memory re-ranks internally; Brain
# then applies its own relevance floor + token budget on top. Small on purpose:
# this is per-turn context, not a search results page.
MEMORY_RECALL_K = _env_int("MEMORY_RECALL_K", 6)

# Relevance gate — two parts, because the embedding space is compressed.
#
# recall() returns a `similarity` in ~(0.35, 1.0] (1/(1+dist) over normalised
# embeddings). In that space even unrelated sentences score ~0.45, so an
# absolute floor alone can't separate signal from noise across queries. So:
#
#   (a) absolute floor  — a weak sanity gate: nothing this weak is ever relevant.
#   (b) relative margin — the real gate: keep the best hit, then keep others only
#       if they sit within this margin of it. This adapts to each query's own
#       similarity scale instead of trusting one global number, so "the gym
#       closes at 10pm" is dropped from an "Aurora rebrand" query even though its
#       absolute similarity clears the floor.
# Floor calibrated against bge-small-en-v1.5: genuine topic matches land ~0.63+,
# generically-similar noise ~0.42–0.52, so 0.55 sits in the gap. It is a tuning
# value (Learning, §7, may adjust it), not an architectural constant.
MEMORY_MIN_SIMILARITY = _env_float("MEMORY_MIN_SIMILARITY", 0.55)
MEMORY_SIMILARITY_MARGIN = _env_float("MEMORY_SIMILARITY_MARGIN", 0.12)

# Token ceiling for the whole "Relevant Semantic Memories" block. The pipeline
# fills it by score order and stops when the next memory would overflow — this
# is the "respect token limits, do not dump everything" guarantee. Approximated
# as chars/4 to stay tokenizer-dependency-free.
MEMORY_CONTEXT_TOKEN_BUDGET = _env_int("MEMORY_TOKEN_BUDGET", 350)

# Reinforcement gate. After the reply is generated, a recalled memory is
# reinforced (record_access) only if this fraction of its significant words
# actually appear in the reply — i.e. it "survived into the response", not
# merely that recall() returned it.
MEMORY_REINFORCE_MIN_OVERLAP = _env_float("MEMORY_REINFORCE_OVERLAP", 0.5)


# ── Context Engine (Milestone 2.8) ────────────────────────────────────────────
# Section-level budgets and switches for the assembly pipeline in
# context_engine/. Same charter as the 2.3 block above: these are Brain's
# consumption policy (how much of each source one turn may spend), never a
# storage or ranking policy. Defaults are deliberately generous — at typical
# personal-scale state nothing binds and the prompt is unchanged; the ceilings
# exist so a pathological state (hundreds of open tasks) degrades by truncation
# instead of by unbounded prompt growth.

# Global ceiling across every context section (headers included, footer and
# messages excluded). Trimmed in the engine's TRIM_ORDER: most speculative
# sections give way first, open tasks last. 0 disables the global ceiling.
CONTEXT_TOTAL_TOKEN_BUDGET = _env_int("CONTEXT_TOKEN_BUDGET", 2000)

# Knowledge-graph section (the 2.8 behavior change: graph context enters the
# prompt). Entity matching is exact n-gram lookup; these caps bound how much
# of the graph one query can pull in.
GRAPH_CONTEXT_ENABLED = _env_bool("GRAPH_CONTEXT", True)
GRAPH_CONTEXT_MAX_ENTITIES = _env_int("GRAPH_MAX_ENTITIES", 3)
GRAPH_CONTEXT_MAX_EDGES = _env_int("GRAPH_MAX_EDGES", 4)
GRAPH_CONTEXT_TOKEN_BUDGET = _env_int("GRAPH_TOKEN_BUDGET", 250)

# Calendar section. Active only when the composition root injects a source
# (set_calendar_source); the TTL caches the slow AppleScript fetch so a
# multi-turn conversation costs one fetch, not one per turn.
CALENDAR_CONTEXT_ENABLED = _env_bool("CALENDAR_CONTEXT", True)
CALENDAR_CONTEXT_TTL_SECONDS = _env_int("CALENDAR_CONTEXT_TTL", 300)
CALENDAR_CONTEXT_TOKEN_BUDGET = _env_int("CALENDAR_TOKEN_BUDGET", 150)

# Phase-1 flat sections, previously unbudgeted.
TASKS_CONTEXT_TOKEN_BUDGET = _env_int("TASKS_TOKEN_BUDGET", 400)
ACTIVITY_CONTEXT_TOKEN_BUDGET = _env_int("ACTIVITY_TOKEN_BUDGET", 450)
PROFILE_CONTEXT_TOKEN_BUDGET = _env_int("PROFILE_TOKEN_BUDGET", 350)


# ── Entity extraction (Milestone 2.7) ─────────────────────────────────────────
# Brain's knobs for the graph-extraction sweep (extraction.py). Like the 2.3
# block above, these are Brain's *consumption* policy — how much to pull per
# Claude call, how often to give up on a row — not Memory's storage policy.

# Master switch, mirroring SEMANTIC_MEMORY_ENABLED: extraction off means the
# graph simply stops growing; nothing else degrades.
ENTITY_EXTRACTION_ENABLED = _env_bool("ENTITY_EXTRACTION", True)

# Memories per Claude call. Big enough to amortize the call over a turn's
# typical 1–3 new memories plus backlog, small enough that one response stays
# well inside the output ceiling.
EXTRACTION_BATCH_SIZE = _env_int("EXTRACTION_BATCH_SIZE", 10)

# A memory that fails extraction this many times is left alone (poison-pill
# guard). Its structured/semantic behavior is untouched — it just never
# contributes graph rows.
EXTRACTION_MAX_ATTEMPTS = _env_int("EXTRACTION_MAX_ATTEMPTS", 3)

# Batches per sweep — caps one run's Claude spend when draining a large
# backlog (first run over a pre-2.7 database). The remainder keeps its place
# in the FIFO queue for the next sweep.
EXTRACTION_MAX_BATCHES = _env_int("EXTRACTION_MAX_BATCHES", 5)


def check_api_config() -> None:
    if not CLAUDE_API_KEY:
        print("[error] Missing NOVA_CLAUDE_API_KEY.")
        print("Add it to .env:  NOVA_CLAUDE_API_KEY=sk-ant-...")
        sys.exit(1)
