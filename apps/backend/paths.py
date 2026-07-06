"""Shared backend paths for code, repo root, and persisted data."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parent.parent

_data_dir_env = os.environ.get("NOVA_DATA_DIR", "").strip()
if _data_dir_env:
    _data_candidate = Path(_data_dir_env).expanduser()
    DATA_ROOT = _data_candidate if _data_candidate.is_absolute() else (REPO_ROOT / _data_candidate)
else:
    DATA_ROOT = REPO_ROOT / "data"

DATA_ROOT = DATA_ROOT.resolve()

ASSETS_ROOT = (REPO_ROOT / "assets").resolve()
CONFIG_ROOT = (REPO_ROOT / "config").resolve()
MODELS_ROOT = (REPO_ROOT / "models").resolve()
