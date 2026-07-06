"""Shared SQLite connection helper. Not part of the public memory API."""

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    from paths import BACKEND_ROOT, DATA_ROOT, REPO_ROOT
except ModuleNotFoundError:  # package-style import fallback
    from apps.backend.paths import BACKEND_ROOT, DATA_ROOT, REPO_ROOT

DB_PATH = DATA_ROOT / "nova.db"
LANCEDB_PATH = DATA_ROOT / "nova_lancedb"

LEGACY_DB_PATHS = [
    DATA_ROOT / "rai.db",
    REPO_ROOT / "nova.db",
    REPO_ROOT / "rai.db",
    BACKEND_ROOT / "nova.db",
    BACKEND_ROOT / "rai.db",
]
LEGACY_LANCEDB_PATHS = [
    DATA_ROOT / "rai_lancedb",
    REPO_ROOT / "nova_lancedb",
    REPO_ROOT / "rai_lancedb",
    BACKEND_ROOT / "nova_lancedb",
    BACKEND_ROOT / "rai_lancedb",
]

_STORAGE_MIGRATION_DONE = False
STORAGE_MIGRATION_STATUS = {"db_migrated": False, "lancedb_migrated": False}


def _migrate_file_if_needed(src: Path, dst: Path) -> bool:
    """Copy old storage file to new path, then best-effort remove old file."""
    if dst.exists() or not src.exists() or not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    try:
        src.unlink()
    except OSError:
        pass
    return True


def _migrate_dir_if_needed(src: Path, dst: Path) -> bool:
    """Copy old storage directory to new path, then best-effort remove old dir."""
    if dst.exists() or not src.exists() or not src.is_dir():
        return False
    shutil.copytree(src, dst)
    try:
        shutil.rmtree(src)
    except OSError:
        pass
    return True


def ensure_storage_paths() -> None:
    """One-time path migration from legacy Rai storage names to Nova names."""
    global _STORAGE_MIGRATION_DONE
    if _STORAGE_MIGRATION_DONE:
        return
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    STORAGE_MIGRATION_STATUS["db_migrated"] = any(
        _migrate_file_if_needed(path, DB_PATH) for path in LEGACY_DB_PATHS
    )
    STORAGE_MIGRATION_STATUS["lancedb_migrated"] = any(
        _migrate_dir_if_needed(path, LANCEDB_PATH) for path in LEGACY_LANCEDB_PATHS
    )
    _STORAGE_MIGRATION_DONE = True


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(rows: bool = False):
    ensure_storage_paths()
    con = sqlite3.connect(DB_PATH)
    if rows:
        con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


ensure_storage_paths()
