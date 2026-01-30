"""Common debug logging utility."""

from __future__ import annotations

import datetime
import os
from pathlib import Path


def debug_log(message: str, *, module: str) -> None:
    """Write debug message to log file.

    Args:
        message: Log message.
        module: Module name for the log prefix.
    """
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] {module}: {message}\n")
    except Exception:
        return
