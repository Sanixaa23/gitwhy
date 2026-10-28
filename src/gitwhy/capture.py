"""Record the last failed git command on disk and read it back.

The shell wrapper (`gitwhy shell-init`) calls `gitwhy capture-exit` after a
failed git command; a bare `gitwhy` reads that record.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

MAX_AGE = 600.0   # seconds


def cache_dir() -> str:
    """Platform-appropriate cache directory. Uses LOCALAPPDATA on Windows."""
    base = (
        os.environ.get("GITWHY_CACHE")
        or os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("LOCALAPPDATA")
        or os.path.join(os.path.expanduser("~"), ".cache")
    )
    return os.path.join(base, "gitwhy")


def record_path() -> str:
    return os.path.join(cache_dir(), "last.json")


def write(command: str, exit_code: int, stdout: str, stderr: str,
          repo: str = ".") -> str:
    """Record the last failed command; return the path written."""
    record = {
        "command": command,
        "exit": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "repo": os.path.abspath(repo),
        "time": time.time(),
    }
    path = record_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path


def read() -> Optional[dict]:
    """Read the last record; None when missing or corrupt."""
    try:
        with open(record_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def is_valid(record: Optional[dict], repo: str, max_age: float = MAX_AGE) -> bool:
    """Does this record belong to THIS repository and the recent past?

    Two guards: a record left behind in another repository must not be applied
    here, and an error from hours ago must not be mistaken for the answer to
    today's command. The command-based rules depend on this check.
    """
    if not record:
        return False
    recorded = os.path.normcase(os.path.abspath(record.get("repo") or ""))
    current = os.path.normcase(os.path.abspath(repo))
    if recorded != current:
        return False
    try:
        return (time.time() - float(record.get("time", 0))) <= max_age
    except (TypeError, ValueError):
        return False


def command(record: Optional[dict]) -> Optional[str]:
    return (record or {}).get("command") or None


def error_text(record: Optional[dict]) -> str:
    """Extract the text to decide on from a record.

    stdout and stderr come back together: git writes some errors (CONFLICT)
    to stdout. Verified by fixture test.
    """
    if not record:
        return ""
    return "\n".join(x for x in (record.get("stderr"), record.get("stdout")) if x)
