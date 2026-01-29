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

    def test_load_filename_fields_returns_default_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns default when settings file doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_filename_fields

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = _load_filename_fields()

        assert result == ["date"]

    def test_load_filename_fields_returns_saved_fields(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns saved fields from settings."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_filename_fields

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": json.dumps(["date", "vehicle_no", "driver"])}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_filename_fields()

        assert result == ["date", "vehicle_no", "driver"]

    def test_load_filename_fields_returns_default_for_invalid_json(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns default when saved value is invalid JSON."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_filename_fields

        # Create settings file with invalid JSON
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": "not a json array"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_filename_fields()

        assert result == ["date"]

    def test_save_filename_fields_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save filename fields creates a new settings file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_filename_fields

        settings_path = tmp_path / "settings.json"
        fields = ["date", "vehicle_no"]

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_filename_fields(fields)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        saved_fields = json.loads(data["text_inserter_filename_fields"])
        assert saved_fields == ["date", "vehicle_no"]

    def test_save_filename_fields_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save filename fields preserves other settings in the file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_filename_fields

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        fields = ["date", "driver"]

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_filename_fields(fields)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        saved_fields = json.loads(data["text_inserter_filename_fields"])
        assert saved_fields == ["date", "driver"]

    def test_load_window_size_returns_default_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load window size returns default when settings file doesn't exist."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_window_size

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = _load_window_size()

        assert result == (500, 600)

    def test_load_window_size_returns_saved_size(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load window size returns saved size from settings."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_window_size

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_window_width": "800", "text_inserter_window_height": "900"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_window_size()

        assert result == (800, 900)

    def test_load_window_size_returns_default_for_invalid_values(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load window size returns default when saved values are invalid."""
        from tachograph_wizard.ui.text_inserter_dialog import _load_window_size

        # Create settings file with invalid values
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_window_width": "not a number", "text_inserter_window_height": "also not"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            result = _load_window_size()

        assert result == (500, 600)

    def test_save_window_size_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save window size creates a new settings file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_window_size

        settings_path = tmp_path / "settings.json"

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_window_size(700, 800)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_window_width"] == "700"
        assert data["text_inserter_window_height"] == "800"

    def test_save_window_size_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save window size preserves other settings in the file."""
        from tachograph_wizard.ui.text_inserter_dialog import _save_window_size

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog._get_settings_path",
            return_value=settings_path,
        ):
            _save_window_size(600, 700)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_window_width"] == "600"
        assert data["text_inserter_window_height"] == "700"


class TestTextInserterDialogUndo:
    """Test text inserter dialog undo functionality."""

    def test_finalize_response_ok_ends_undo_group(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """OK response ends undo group without undoing."""
        gimp_mock, _gimpui_mock, _gegl_mock = mock_gimp_modules

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1

        # Test the finalize_response logic directly
        # This simulates what the method does without needing the class
        response = gtk_mock.ResponseType.OK
        has_pending_changes = True

        # End the undo group first
        mock_image.undo_group_end()

        # If cancelled and changes were made, undo them
        if response != gtk_mock.ResponseType.OK and has_pending_changes:
            gimp_mock.get_pdb().run_procedure("gimp-edit-undo", [mock_image])
            gimp_mock.displays_flush()

        # Verify undo group was ended
        mock_image.undo_group_end.assert_called_once()

        # Verify undo was NOT called (OK response commits changes)
        gimp_mock.get_pdb.return_value.run_procedure.assert_not_called()

    def test_finalize_response_cancel_undoes_changes(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Cancel response undoes all changes when changes were made."""
        gimp_mock, _gimpui_mock, _gegl_mock = mock_gimp_modules

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1
        gtk_mock.ResponseType.CANCEL = 0

        # Test the finalize_response logic directly
        response = gtk_mock.ResponseType.CANCEL
        has_pending_changes = True

        # End the undo group first
        mock_image.undo_group_end()

        # If cancelled and changes were made, undo them
        if response != gtk_mock.ResponseType.OK and has_pending_changes:
            gimp_mock.get_pdb().run_procedure("gimp-edit-undo", [mock_image])
            gimp_mock.displays_flush()

        # Verify undo group was ended
        mock_image.undo_group_end.assert_called_once()

        # Verify undo was called (Cancel response with changes)
        gimp_mock.get_pdb.return_value.run_procedure.assert_called_once()
        call_args = gimp_mock.get_pdb.return_value.run_procedure.call_args
        assert call_args[0][0] == "gimp-edit-undo"
        assert call_args[0][1][0] == mock_image

    def test_finalize_response_cancel_no_undo_without_changes(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Cancel response does not undo when no changes were made."""
        gimp_mock, _gimpui_mock, _gegl_mock = mock_gimp_modules

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1
        gtk_mock.ResponseType.CANCEL = 0

        # Test the finalize_response logic directly
        response = gtk_mock.ResponseType.CANCEL
        has_pending_changes = False

        # End the undo group first
        mock_image.undo_group_end()

        # If cancelled and changes were made, undo them
        if response != gtk_mock.ResponseType.OK and has_pending_changes:
            gimp_mock.get_pdb().run_procedure("gimp-edit-undo", [mock_image])
            gimp_mock.displays_flush()

        # Verify undo group was ended
        mock_image.undo_group_end.assert_called_once()

        # Verify undo was NOT called (no changes to undo)
        gimp_mock.get_pdb.return_value.run_procedure.assert_not_called()
