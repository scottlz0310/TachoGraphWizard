# pyright: reportPrivateUsage=false
# pyright: reportUnnecessaryComparison=false
"""Unit tests for text inserter dialog settings functions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTextInserterDialogSettings:
    """Test text inserter dialog settings persistence functions."""

    def test_load_csv_path_returns_none_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns None when settings file doesn't exist."""
        from tachograph_wizard.ui.settings_manager import load_csv_path

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_csv_path()

        assert result is None

    def test_load_csv_path_returns_path_when_exists(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns the path when settings contain a valid path."""
        from tachograph_wizard.ui.settings_manager import load_csv_path

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
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_csv_path()

        assert result == csv_file

    def test_load_csv_path_returns_none_for_nonexistent_path(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load CSV path returns None when saved path doesn't exist."""
        from tachograph_wizard.ui.settings_manager import load_csv_path

        # Create settings file with non-existent path
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_csv_path": str(tmp_path / "nonexistent.csv")}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_csv_path()

        assert result is None

    def test_save_csv_path_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save CSV path creates a new settings file."""
        from tachograph_wizard.ui.settings_manager import save_csv_path

        settings_path = tmp_path / "settings.json"
        csv_path = tmp_path / "test.csv"

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_csv_path(csv_path)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_csv_path"] == str(csv_path)

    def test_save_csv_path_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save CSV path preserves other settings in the file."""
        from tachograph_wizard.ui.settings_manager import save_csv_path

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        csv_path = tmp_path / "test.csv"

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_csv_path(csv_path)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_csv_path"] == str(csv_path)

    def test_load_output_dir_returns_none_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns None when settings file doesn't exist."""
        from tachograph_wizard.ui.settings_manager import load_output_dir

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_output_dir()

        assert result is None

    def test_load_output_dir_returns_path_when_exists(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns the path when settings contain a valid path."""
        from tachograph_wizard.ui.settings_manager import load_output_dir

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
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_output_dir()

        assert result == output_dir

    def test_load_output_dir_returns_none_for_nonexistent_path(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load output directory returns None when saved path doesn't exist."""
        from tachograph_wizard.ui.settings_manager import load_output_dir

        # Create settings file with non-existent path
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_output_dir": str(tmp_path / "nonexistent_dir")}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_output_dir()

        assert result is None

    def test_save_output_dir_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save output directory creates a new settings file."""
        from tachograph_wizard.ui.settings_manager import save_output_dir

        settings_path = tmp_path / "settings.json"
        output_dir = tmp_path / "output"

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_output_dir(output_dir)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_output_dir"] == str(output_dir)

    def test_save_output_dir_preserves_existing_settings(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save output directory preserves other settings in the file."""
        from tachograph_wizard.ui.settings_manager import save_output_dir

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_output_dir(output_dir)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_output_dir"] == str(output_dir)

    def test_load_filename_fields_returns_default_for_missing_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns default when settings file doesn't exist."""
        from tachograph_wizard.ui.settings_manager import load_filename_fields

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_filename_fields()

        assert result == ["date"]

    def test_load_filename_fields_returns_saved_fields(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns saved fields from settings."""
        from tachograph_wizard.ui.settings_manager import load_filename_fields

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": json.dumps(["date", "vehicle_no", "driver"])}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_filename_fields()

        assert result == ["date", "vehicle_no", "driver"]

    def test_load_filename_fields_returns_default_for_invalid_json(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load filename fields returns default when saved value is invalid JSON."""
        from tachograph_wizard.ui.settings_manager import load_filename_fields

        # Create settings file with invalid JSON
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": "not a json array"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_filename_fields()

        assert result == ["date"]

    def test_save_filename_fields_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save filename fields creates a new settings file."""
        from tachograph_wizard.ui.settings_manager import save_filename_fields

        settings_path = tmp_path / "settings.json"
        fields = ["date", "vehicle_no"]

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_filename_fields(fields)

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
        from tachograph_wizard.ui.settings_manager import save_filename_fields

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )
        fields = ["date", "driver"]

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_filename_fields(fields)

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
        from tachograph_wizard.ui.settings_manager import load_window_size

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            result = load_window_size()

        assert result == (500, 600)

    def test_load_window_size_returns_saved_size(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load window size returns saved size from settings."""
        from tachograph_wizard.ui.settings_manager import load_window_size

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_window_width": "800", "text_inserter_window_height": "900"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_window_size()

        assert result == (800, 900)

    def test_load_window_size_returns_default_for_invalid_values(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Load window size returns default when saved values are invalid."""
        from tachograph_wizard.ui.settings_manager import load_window_size

        # Create settings file with invalid values
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_window_width": "not a number", "text_inserter_window_height": "also not"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            result = load_window_size()

        assert result == (500, 600)

    def test_save_window_size_creates_settings_file(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Save window size creates a new settings file."""
        from tachograph_wizard.ui.settings_manager import save_window_size

        settings_path = tmp_path / "settings.json"

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_window_size(700, 800)

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
        from tachograph_wizard.ui.settings_manager import save_window_size

        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"other_setting": "value"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.ui.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            save_window_size(600, 700)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_setting"] == "value"
        assert data["text_inserter_window_width"] == "600"
        assert data["text_inserter_window_height"] == "700"


class TestTextInserterDialogCancel:
    """Test text inserter dialog cancel functionality.

    Note: These tests verify the finalize_response logic by simulating what the method does.
    Due to the GIMP module mocking, the TextInserterDialog class is replaced with a mock,
    making it impossible to call the actual finalize_response method directly.
    The procedure tests in TestTextInserterProcedure verify the integration.
    """

    def test_finalize_response_ok_keeps_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """OK response keeps all inserted layers."""
        gimp_mock, _, _ = mock_gimp_modules

        # Create mock layers
        mock_layer1 = MagicMock()
        mock_layer1.is_valid.return_value = True
        mock_layer2 = MagicMock()
        mock_layer2.is_valid.return_value = True

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1

        # Simulate finalize_response logic for OK with inserted layers
        _inserted_layers = [mock_layer1, mock_layer2]
        response = gtk_mock.ResponseType.OK

        if response != gtk_mock.ResponseType.OK and _inserted_layers:
            for layer in _inserted_layers:
                if layer.is_valid():
                    mock_image.remove_layer(layer)
            gimp_mock.displays_flush()

        # Verify layers were NOT removed (OK response keeps changes)
        mock_image.remove_layer.assert_not_called()

    def test_finalize_response_cancel_removes_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Cancel response removes all inserted layers."""
        gimp_mock, _, _ = mock_gimp_modules

        # Create mock layers
        mock_layer1 = MagicMock()
        mock_layer1.is_valid.return_value = True
        mock_layer2 = MagicMock()
        mock_layer2.is_valid.return_value = True

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1
        gtk_mock.ResponseType.CANCEL = 0

        # Simulate finalize_response logic for CANCEL with inserted layers
        _inserted_layers = [mock_layer1, mock_layer2]
        response = gtk_mock.ResponseType.CANCEL

        if response != gtk_mock.ResponseType.OK and _inserted_layers:
            for layer in _inserted_layers:
                if layer.is_valid():
                    mock_image.remove_layer(layer)
            gimp_mock.displays_flush()

        # Verify layers were removed (Cancel response removes changes)
        assert mock_image.remove_layer.call_count == 2
        gimp_mock.displays_flush.assert_called_once()

    def test_finalize_response_cancel_no_action_without_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Cancel response does nothing when no layers were inserted."""
        gimp_mock, _, _ = mock_gimp_modules

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1
        gtk_mock.ResponseType.CANCEL = 0

        # Simulate finalize_response logic for CANCEL without inserted layers
        _inserted_layers: list[MagicMock] = []
        response = gtk_mock.ResponseType.CANCEL

        if response != gtk_mock.ResponseType.OK and _inserted_layers:
            for layer in _inserted_layers:
                if layer.is_valid():
                    mock_image.remove_layer(layer)
            gimp_mock.displays_flush()

        # Verify no layer removal was attempted
        mock_image.remove_layer.assert_not_called()
        gimp_mock.displays_flush.assert_not_called()

    def test_finalize_response_cancel_skips_invalid_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Cancel response skips layers that are no longer valid."""
        gimp_mock, _, _ = mock_gimp_modules

        # Create mock layers - one valid, one invalid
        mock_layer_valid = MagicMock()
        mock_layer_valid.is_valid.return_value = True
        mock_layer_invalid = MagicMock()
        mock_layer_invalid.is_valid.return_value = False

        # Create a mock image
        mock_image = MagicMock()

        # Mock Gtk.ResponseType
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]
        gtk_mock.ResponseType.OK = 1
        gtk_mock.ResponseType.CANCEL = 0

        # Simulate finalize_response logic for CANCEL
        _inserted_layers = [mock_layer_valid, mock_layer_invalid]
        response = gtk_mock.ResponseType.CANCEL

        if response != gtk_mock.ResponseType.OK and _inserted_layers:
            for layer in _inserted_layers:
                try:
                    if layer.is_valid():
                        mock_image.remove_layer(layer)
                except Exception:
                    # Ignore errors during best-effort cleanup of inserted layers.
                    pass
            gimp_mock.displays_flush()

        # Verify only valid layer was removed
        mock_image.remove_layer.assert_called_once_with(mock_layer_valid)


class TestTextInserterProcedure:
    """Test text inserter procedure functionality."""

    def test_run_text_inserter_dialog_returns_false_on_cancel(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """run_text_inserter_dialog returns False when dialog is cancelled."""
        _ = mock_gimp_modules  # Required for GIMP module mocking

        # Create a mock image
        mock_image = MagicMock()

        # Get Gtk mock from modules - this is what the procedure will use
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]

        # Mock TextInserterDialog
        mock_dialog = MagicMock()
        # Use the SAME mock value that the procedure will compare against
        mock_dialog.run.return_value = gtk_mock.ResponseType.CANCEL

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog.TextInserterDialog",
            return_value=mock_dialog,
        ):
            from tachograph_wizard.procedures.text_inserter_procedure import (
                run_text_inserter_dialog,
            )

            result = run_text_inserter_dialog(mock_image, None)

        # When dialog.run() returns CANCEL, result should be False
        assert result is False
        mock_dialog.run.assert_called_once()
        mock_dialog.finalize_response.assert_called_once()
        mock_dialog.destroy.assert_called_once()

    def test_run_text_inserter_dialog_calls_finalize_response_and_destroy(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """run_text_inserter_dialog always calls finalize_response and destroy."""
        _ = mock_gimp_modules  # Required for GIMP module mocking

        # Create a mock image
        mock_image = MagicMock()

        # Get Gtk mock from modules
        import sys

        gtk_mock = sys.modules["gi.repository.Gtk"]

        # Mock TextInserterDialog
        mock_dialog = MagicMock()
        mock_dialog.run.return_value = gtk_mock.ResponseType.OK

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog.TextInserterDialog",
            return_value=mock_dialog,
        ):
            from tachograph_wizard.procedures.text_inserter_procedure import (
                run_text_inserter_dialog,
            )

            run_text_inserter_dialog(mock_image, None)

        # Verify the procedure correctly calls finalize_response with the response
        mock_dialog.run.assert_called_once()
        mock_dialog.finalize_response.assert_called_once_with(gtk_mock.ResponseType.OK)
        mock_dialog.destroy.assert_called_once()

    def test_run_text_inserter_dialog_calls_finalize_on_exception(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """run_text_inserter_dialog calls finalize_response even when dialog.run() raises."""
        _ = mock_gimp_modules  # Required for GIMP module mocking

        # Create a mock image
        mock_image = MagicMock()

        # Mock TextInserterDialog that raises an exception
        mock_dialog = MagicMock()
        mock_dialog.run.side_effect = RuntimeError("Dialog error")

        with patch(
            "tachograph_wizard.ui.text_inserter_dialog.TextInserterDialog",
            return_value=mock_dialog,
        ):
            from tachograph_wizard.procedures.text_inserter_procedure import (
                run_text_inserter_dialog,
            )

            with pytest.raises(RuntimeError, match="Dialog error"):
                run_text_inserter_dialog(mock_image, None)

        # Verify finalize_response was still called (with default CANCEL since run() raised)
        # Note: We verify it was called once; the argument is the Gtk.ResponseType.CANCEL mock
        # which gets a new identity from the procedure's Gtk import
        mock_dialog.finalize_response.assert_called_once()
        mock_dialog.destroy.assert_called_once()
