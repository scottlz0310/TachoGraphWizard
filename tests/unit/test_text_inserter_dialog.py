# pyright: reportPrivateUsage=false
"""Unit tests for text inserter dialog settings functions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestTextInserterDialogSettings:
    """Test text inserter dialog settings persistence functions."""

    def test_load_csv_path_returns_none_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns None when settings file doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_csv_path

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = _load_csv_path()

        assert result is None

    def test_load_csv_path_returns_path_when_exists(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns the path when settings contain a valid path."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_csv_path

        # Create a CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\n1,2\n", encoding="utf-8")

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_csv_path": str(csv_file)}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_csv_path()

        assert result == csv_file

    def test_load_csv_path_returns_none_for_nonexistent_path(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns None when saved path doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_csv_path

        # Create settings file with non-existent path
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_csv_path": str(tmp_path / "nonexistent.csv")}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_csv_path()

        assert result is None

    def test_save_csv_path_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save CSV path creates a new settings file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_csv_path

        settings_path = tmp_path / "settings.json"
        csv_path = tmp_path / "test.csv"

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_csv_path(csv_path)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_csv_path"] == str(csv_path)

    def test_save_csv_path_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save CSV path preserves other settings in the file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_csv_path

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        csv_path = tmp_path / "test.csv"

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_csv_path(csv_path)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_csv_path"] == str(csv_path)

    def test_load_output_dir_returns_none_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns None when settings file doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_output_dir

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = _load_output_dir()

        assert result is None

    def test_load_output_dir_returns_path_when_exists(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns the path when settings contain a valid path."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_output_dir

        # Create an output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_output_dir": str(output_dir)}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_output_dir()

        assert result == output_dir

    def test_load_output_dir_returns_none_for_nonexistent_path(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns None when saved path doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_output_dir

        # Create settings file with non-existent path
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_output_dir": str(tmp_path / "nonexistent_dir")}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_output_dir()

        assert result is None

    def test_save_output_dir_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save output directory creates a new settings file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_output_dir

        settings_path = tmp_path / "settings.json"
        output_dir = tmp_path / "output"

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_output_dir(output_dir)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_output_dir"] == str(output_dir)

    def test_save_output_dir_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save output directory preserves other settings in the file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_output_dir

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_output_dir(output_dir)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_output_dir"] == str(output_dir)
