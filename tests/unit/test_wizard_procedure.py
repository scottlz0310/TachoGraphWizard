# pyright: reportPrivateUsage=false
"""Unit tests for wizard_procedure settings functions."""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath
from unittest.mock import MagicMock, patch


class TestWizardProcedureSettings:
    """Test wizard procedure settings persistence functions."""

    @patch("tachograph_wizard.procedures.wizard_procedure.os.name", "posix")
    @patch("tachograph_wizard.procedures.wizard_procedure.os.environ", {"XDG_CONFIG_HOME": "/test/config"})
    def test_get_settings_path_xdg_config(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _get_settings_path uses XDG_CONFIG_HOME on Linux."""
        from tachograph_wizard.procedures.wizard_procedure import _get_settings_path

        result = _get_settings_path()
        assert str(result) == "/test/config/tachograph_wizard/settings.json"

    @patch("tachograph_wizard.procedures.wizard_procedure.os.name", "posix")
    @patch("tachograph_wizard.procedures.wizard_procedure.os.environ", {})
    @patch("tachograph_wizard.procedures.wizard_procedure.Path.home")
    def test_get_settings_path_home_config(
        self,
        mock_home: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _get_settings_path falls back to ~/.config on Linux."""
        from tachograph_wizard.procedures.wizard_procedure import _get_settings_path

        mock_home.return_value = Path("/home/user")
        result = _get_settings_path()
        assert str(result) == "/home/user/.config/tachograph_wizard/settings.json"

    @patch("tachograph_wizard.procedures.wizard_procedure.os.name", "nt")
    @patch("tachograph_wizard.procedures.wizard_procedure.os.environ", {"APPDATA": "C:\\Users\\Test\\AppData"})
    def test_get_settings_path_windows_appdata(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _get_settings_path uses APPDATA on Windows."""
        from tachograph_wizard.procedures.wizard_procedure import _get_settings_path

        with patch("tachograph_wizard.procedures.wizard_procedure.Path", PureWindowsPath):
            result = _get_settings_path()

        assert str(result) == "C:\\Users\\Test\\AppData\\tachograph_wizard\\settings.json"

    def test_load_last_output_dir_file_not_found(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _load_last_output_dir returns default when file doesn't exist."""
        from tachograph_wizard.procedures.wizard_procedure import _load_last_output_dir

        default_dir = tmp_path / "default"
        result = _load_last_output_dir(default_dir)
        assert result == default_dir

    def test_load_last_output_dir_valid_json(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _load_last_output_dir loads valid JSON settings."""
        from tachograph_wizard.procedures.wizard_procedure import _load_last_output_dir

        # Create settings file
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        saved_dir = tmp_path / "saved"
        saved_dir.mkdir()

        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps({"wizard_last_output_dir": str(saved_dir)}))

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            default_dir = tmp_path / "default"
            result = _load_last_output_dir(default_dir)
            assert result == saved_dir

    def test_load_last_output_dir_nonexistent_directory(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _load_last_output_dir returns default when saved dir doesn't exist."""
        from tachograph_wizard.procedures.wizard_procedure import _load_last_output_dir

        # Create settings file with non-existent directory
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps({"wizard_last_output_dir": "/nonexistent/path"}))

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            default_dir = tmp_path / "default"
            result = _load_last_output_dir(default_dir)
            assert result == default_dir

    def test_load_last_output_dir_invalid_json(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _load_last_output_dir handles invalid JSON gracefully."""
        from tachograph_wizard.procedures.wizard_procedure import _load_last_output_dir

        # Create settings file with invalid JSON
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text("invalid json {")

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            default_dir = tmp_path / "default"
            result = _load_last_output_dir(default_dir)
            assert result == default_dir

    def test_load_last_output_dir_non_dict_json(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _load_last_output_dir handles non-dict JSON gracefully."""
        from tachograph_wizard.procedures.wizard_procedure import _load_last_output_dir

        # Create settings file with JSON array instead of dict
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps(["not", "a", "dict"]))

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            default_dir = tmp_path / "default"
            result = _load_last_output_dir(default_dir)
            assert result == default_dir

    def test_save_last_output_dir_creates_new_file(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _save_last_output_dir creates new settings file."""
        from tachograph_wizard.procedures.wizard_procedure import _save_last_output_dir

        # Setup
        settings_file = tmp_path / "settings" / "settings.json"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            _save_last_output_dir(output_dir)

            # Verify file was created
            assert settings_file.exists()
            data = json.loads(settings_file.read_text())
            assert data["wizard_last_output_dir"] == str(output_dir)

    def test_save_last_output_dir_updates_existing_file(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _save_last_output_dir updates existing settings file."""
        from tachograph_wizard.procedures.wizard_procedure import _save_last_output_dir

        # Create existing settings file
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps({"other_setting": "value"}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            _save_last_output_dir(output_dir)

            # Verify file was updated
            data = json.loads(settings_file.read_text())
            assert data["wizard_last_output_dir"] == str(output_dir)
            assert data["other_setting"] == "value"  # Preserves existing settings

    def test_save_last_output_dir_handles_invalid_existing_json(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _save_last_output_dir handles invalid existing JSON."""
        from tachograph_wizard.procedures.wizard_procedure import _save_last_output_dir

        # Create existing settings file with invalid JSON
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text("invalid json {")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            _save_last_output_dir(output_dir)

            # Verify file was created with valid JSON
            data = json.loads(settings_file.read_text())
            assert data["wizard_last_output_dir"] == str(output_dir)

    def test_save_last_output_dir_handles_non_dict_existing_json(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _save_last_output_dir handles non-dict existing JSON."""
        from tachograph_wizard.procedures.wizard_procedure import _save_last_output_dir

        # Create existing settings file with JSON array
        settings_dir = tmp_path / "settings"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps(["not", "a", "dict"]))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock _get_settings_path to return our test file
        with patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file):
            _save_last_output_dir(output_dir)

            # Verify file was created with valid dict JSON
            data = json.loads(settings_file.read_text())
            assert isinstance(data, dict)
            assert data["wizard_last_output_dir"] == str(output_dir)

    def test_save_last_output_dir_handles_permission_error(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test _save_last_output_dir handles permission errors gracefully."""
        from tachograph_wizard.procedures.wizard_procedure import _save_last_output_dir

        # Setup
        settings_file = tmp_path / "settings" / "settings.json"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock _get_settings_path and mkdir to raise PermissionError
        with (
            patch("tachograph_wizard.procedures.wizard_procedure._get_settings_path", return_value=settings_file),
            patch.object(Path, "mkdir", side_effect=PermissionError("No permission")),
        ):
            # Should not raise an exception
            _save_last_output_dir(output_dir)
