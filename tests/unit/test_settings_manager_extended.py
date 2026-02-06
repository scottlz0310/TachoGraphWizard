# pyright: reportPrivateUsage=false
"""Extended unit tests for settings_manager - covers missing branches."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from unittest.mock import patch


class TestSettingsManagerParseDateString:
    """Test parse_date_string function."""

    def test_parse_iso_format(self) -> None:
        """Parse YYYY-MM-DD format."""
        from tachograph_wizard.core.settings_manager import parse_date_string

        result = parse_date_string("2024-06-15")
        assert result == datetime.date(2024, 6, 15)

    def test_parse_slash_format(self) -> None:
        """Parse YYYY/MM/DD format."""
        from tachograph_wizard.core.settings_manager import parse_date_string

        result = parse_date_string("2024/06/15")
        assert result == datetime.date(2024, 6, 15)

    def test_parse_dot_format(self) -> None:
        """Parse YYYY.MM.DD format."""
        from tachograph_wizard.core.settings_manager import parse_date_string

        result = parse_date_string("2024.06.15")
        assert result == datetime.date(2024, 6, 15)

    def test_parse_invalid_date(self) -> None:
        """Invalid date string returns None."""
        from tachograph_wizard.core.settings_manager import parse_date_string

        result = parse_date_string("not-a-date")
        assert result is None

    def test_parse_empty_string(self) -> None:
        """Empty string returns None."""
        from tachograph_wizard.core.settings_manager import parse_date_string

        result = parse_date_string("")
        assert result is None


class TestSettingsManagerCorruptFile:
    """Test settings loading with corrupt/invalid JSON."""

    def test_load_setting_corrupt_json(self, tmp_path: Path) -> None:
        """Loading from corrupt JSON returns None."""
        from tachograph_wizard.core.settings_manager import _load_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{invalid json", encoding="utf-8")

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_setting("some_key")

        assert result is None

    def test_load_setting_missing_key(self, tmp_path: Path) -> None:
        """Loading a non-existent key returns None."""
        from tachograph_wizard.core.settings_manager import _load_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"other_key": "value"}', encoding="utf-8")

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_setting("missing_key")

        assert result is None

    def test_save_setting_creates_directory(self, tmp_path: Path) -> None:
        """_save_setting creates parent directory if needed."""
        from tachograph_wizard.core.settings_manager import _save_setting

        settings_path = tmp_path / "subdir" / "settings.json"

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            _save_setting("key", "value")

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["key"] == "value"

    def test_save_setting_merges_with_existing(self, tmp_path: Path) -> None:
        """_save_setting merges with existing settings."""
        from tachograph_wizard.core.settings_manager import _save_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"existing": "data"}', encoding="utf-8")

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            _save_setting("new_key", "new_value")

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["existing"] == "data"
        assert data["new_key"] == "new_value"

    def test_save_setting_overwrites_corrupt_file(self, tmp_path: Path) -> None:
        """_save_setting overwrites corrupt existing file."""
        from tachograph_wizard.core.settings_manager import _save_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{corrupt", encoding="utf-8")

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            _save_setting("key", "value")

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data == {"key": "value"}


class TestSettingsManagerLoadPathSetting:
    """Test _load_path_setting function."""

    def test_load_path_setting_existing_path(self, tmp_path: Path) -> None:
        """Load a valid path setting that exists on disk."""
        from tachograph_wizard.core.settings_manager import _load_path_setting

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"test_path": str(target_dir)}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_path_setting("test_path")

        assert result == target_dir

    def test_load_path_setting_nonexistent_path(self, tmp_path: Path) -> None:
        """Returns None when stored path doesn't exist on disk."""
        from tachograph_wizard.core.settings_manager import _load_path_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"test_path": "/nonexistent/path"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_path_setting("test_path")

        assert result is None

    def test_load_path_setting_empty_value(self, tmp_path: Path) -> None:
        """Returns None when stored value is empty string."""
        from tachograph_wizard.core.settings_manager import _load_path_setting

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"test_path": ""}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_path_setting("test_path")

        assert result is None


class TestSettingsManagerLastDate:
    """Test load/save_last_used_date."""

    def test_load_last_used_date_none(self, tmp_path: Path) -> None:
        """Returns None when no date is stored."""
        from tachograph_wizard.core.settings_manager import load_last_used_date

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_last_used_date()

        assert result is None

    def test_load_last_used_date_invalid_format(self, tmp_path: Path) -> None:
        """Returns None when stored date is invalid."""
        from tachograph_wizard.core.settings_manager import load_last_used_date

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_last_date": "not-a-date"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_last_used_date()

        assert result is None


class TestSettingsManagerWindowSize:
    """Test window size load/save."""

    def test_load_window_size_defaults(self, tmp_path: Path) -> None:
        """Returns defaults when no settings exist."""
        from tachograph_wizard.core.settings_manager import load_window_size

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_window_size()

        assert result == (500, 600)

    def test_load_window_size_invalid_values(self, tmp_path: Path) -> None:
        """Returns defaults when stored values are not valid integers."""
        from tachograph_wizard.core.settings_manager import load_window_size

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "text_inserter_window_width": "abc",
                    "text_inserter_window_height": "xyz",
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_window_size()

        assert result == (500, 600)


class TestSettingsManagerFilenameFields:
    """Test filename fields load/save."""

    def test_load_filename_fields_default(self, tmp_path: Path) -> None:
        """Returns default ['date'] when no settings exist."""
        from tachograph_wizard.core.settings_manager import load_filename_fields

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_filename_fields()

        assert result == ["date"]

    def test_load_filename_fields_invalid_json(self, tmp_path: Path) -> None:
        """Returns default when stored value is invalid JSON."""
        from tachograph_wizard.core.settings_manager import load_filename_fields

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": "not-json"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_filename_fields()

        assert result == ["date"]

    def test_load_filename_fields_not_list(self, tmp_path: Path) -> None:
        """Returns default when stored JSON is not a list."""
        from tachograph_wizard.core.settings_manager import load_filename_fields

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": '"just_a_string"'}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_filename_fields()

        assert result == ["date"]


class TestSettingsManagerGetSettingsPath:
    """Test _get_settings_path function for different platforms."""

    def test_get_settings_path_linux(self) -> None:
        """Test path on Linux (non-nt os)."""
        from tachograph_wizard.core.settings_manager import _get_settings_path

        with (
            patch("tachograph_wizard.core.settings_manager.os.name", "posix"),
            patch.dict(
                "os.environ",
                {"XDG_CONFIG_HOME": "/tmp/test_config"},  # noqa: S108
                clear=False,
            ),
        ):
            result = _get_settings_path()

        assert "tachograph_wizard" in str(result)
        assert "settings.json" in str(result)
