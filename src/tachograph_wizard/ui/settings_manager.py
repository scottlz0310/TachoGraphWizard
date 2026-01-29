"""Settings manager for persistent configuration storage.

Provides functions for loading and saving application settings to JSON files.
Settings are stored in the user's configuration directory following platform conventions.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path


def _get_settings_path() -> Path:
    """Get the path to the settings file.

    Returns:
        Path to the settings.json file in the user's config directory.
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "tachograph_wizard" / "settings.json"


def _load_setting(key: str) -> str | None:
    """Load a setting value from the settings file.

    Args:
        key: The setting key to load.

    Returns:
        The setting value as a string, or None if not found.
    """
    settings_path = _get_settings_path()
    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data.get(key)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, TypeError, ValueError):
        # Log warning if we had a debug logger
        pass
    return None


def _save_setting(key: str, value: str) -> None:
    """Save a setting value to the settings file.

    Args:
        key: The setting key to save.
        value: The setting value to save.
    """
    settings_path = _get_settings_path()
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, str] = {}
        if settings_path.exists():
            try:
                with settings_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (json.JSONDecodeError, TypeError, ValueError):
                data = {}
        data[key] = value
        with settings_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=True, indent=2)
    except Exception:
        # Log warning if we had a debug logger
        pass


def _load_path_setting(key: str) -> Path | None:
    """Load a path setting from the settings file.

    Args:
        key: The setting key to load.

    Returns:
        The path if it exists, or None otherwise.
    """
    value = _load_setting(key)
    if value:
        candidate = Path(value)
        if candidate.exists():
            return candidate
    return None


def _parse_date_string(value: str) -> datetime.date | None:
    """Parse a date string in various formats.

    Args:
        value: Date string to parse.

    Returns:
        Parsed date or None if parsing fails.
    """
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.datetime.strptime(value, fmt).replace(tzinfo=datetime.UTC).date()
        except ValueError:
            continue
    return None


def _load_last_used_date() -> datetime.date | None:
    """Load the last used date from settings.

    Returns:
        The last used date or None if not found.
    """
    value = _load_setting("text_inserter_last_date")
    if value:
        try:
            return datetime.date.fromisoformat(value)
        except (TypeError, ValueError):
            pass
    return None


def _save_last_used_date(selected_date: datetime.date) -> None:
    """Save the last used date to settings.

    Args:
        selected_date: The date to save.
    """
    _save_setting("text_inserter_last_date", selected_date.isoformat())


def _load_template_dir(default_dir: Path) -> Path:
    """Load the template directory from settings.

    Args:
        default_dir: Default directory to return if no setting exists.

    Returns:
        The template directory path.
    """
    result = _load_path_setting("text_inserter_template_dir")
    return result if result else default_dir


def _save_template_dir(selected_dir: Path) -> None:
    """Save the template directory to settings.

    Args:
        selected_dir: The directory to save.
    """
    _save_setting("text_inserter_template_dir", str(selected_dir))


def _load_csv_path() -> Path | None:
    """Load the last used CSV file path from settings.

    Returns:
        The CSV file path or None if not found.
    """
    return _load_path_setting("text_inserter_csv_path")


def _save_csv_path(csv_path: Path) -> None:
    """Save the CSV file path to settings.

    Args:
        csv_path: The CSV file path to save.
    """
    _save_setting("text_inserter_csv_path", str(csv_path))


def _load_output_dir() -> Path | None:
    """Load the last used output directory from settings.

    Returns:
        The output directory path or None if not found.
    """
    return _load_path_setting("text_inserter_output_dir")


def _save_output_dir(output_dir: Path) -> None:
    """Save the output directory to settings.

    Args:
        output_dir: The directory to save.
    """
    _save_setting("text_inserter_output_dir", str(output_dir))


def _load_filename_fields() -> list[str]:
    """Load saved filename field selections.

    Returns:
        List of selected filename fields, defaults to ["date"].
    """
    value = _load_setting("text_inserter_filename_fields")
    if value:
        try:
            fields = json.loads(value)
            if isinstance(fields, list):
                return fields
        except json.JSONDecodeError:
            pass
    return ["date"]  # Default: only date is selected


def _save_filename_fields(fields: list[str]) -> None:
    """Save filename field selections.

    Args:
        fields: List of filename fields to save.
    """
    _save_setting("text_inserter_filename_fields", json.dumps(fields))


def _load_window_size() -> tuple[int, int]:
    """Load saved window size.

    Returns:
        Tuple of (width, height), defaults to (500, 600).
    """
    width = _load_setting("text_inserter_window_width")
    height = _load_setting("text_inserter_window_height")
    try:
        w = int(width) if width else 500
        h = int(height) if height else 600
        return (w, h)
    except (TypeError, ValueError):
        return (500, 600)


def _save_window_size(width: int, height: int) -> None:
    """Save window size.

    Args:
        width: Window width in pixels.
        height: Window height in pixels.
    """
    _save_setting("text_inserter_window_width", str(width))
    _save_setting("text_inserter_window_height", str(height))
