"""Unit tests for Settings class."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSettings:
    """Test Settings class functionality."""

    def test_load_last_used_date_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_last_used_date delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create settings file
        settings_path = tmp_path / "settings.json"
        test_date = datetime.date(2024, 1, 15)
        settings_path.write_text(
            json.dumps({"text_inserter_last_date": test_date.isoformat()}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_last_used_date()

        assert result == test_date

    def test_save_last_used_date_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_last_used_date delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"
        test_date = datetime.date(2024, 1, 15)

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_last_used_date(test_date)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_last_date"] == test_date.isoformat()

    def test_load_template_dir_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_template_dir delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_template_dir": str(template_dir)}),
            encoding="utf-8",
        )

        default_dir = tmp_path / "default"
        default_dir.mkdir()

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_template_dir(default_dir)

        assert result == template_dir

    def test_load_template_dir_returns_default_when_no_setting(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_template_dir returns default when no setting exists."""
        from tachograph_wizard.ui.settings import Settings

        default_dir = tmp_path / "default"
        default_dir.mkdir()

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=tmp_path / "nonexistent" / "settings.json",
        ):
            settings = Settings()
            result = settings.load_template_dir(default_dir)

        assert result == default_dir

    def test_save_template_dir_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_template_dir delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"
        template_dir = tmp_path / "templates"

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_template_dir(template_dir)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_template_dir"] == str(template_dir)

    def test_load_csv_path_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_csv_path delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\n1,2\n", encoding="utf-8")

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_csv_path": str(csv_file)}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_csv_path()

        assert result == csv_file

    def test_save_csv_path_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_csv_path delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"
        csv_path = tmp_path / "test.csv"

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_csv_path(csv_path)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_csv_path"] == str(csv_path)

    def test_load_output_dir_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_output_dir delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_output_dir": str(output_dir)}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_output_dir()

        assert result == output_dir

    def test_save_output_dir_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_output_dir delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"
        output_dir = tmp_path / "output"

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_output_dir(output_dir)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_output_dir"] == str(output_dir)

    def test_load_filename_fields_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_filename_fields delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_filename_fields": json.dumps(["date", "vehicle_no"])}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_filename_fields()

        assert result == ["date", "vehicle_no"]

    def test_save_filename_fields_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_filename_fields delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"
        fields = ["date", "vehicle_no"]

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_filename_fields(fields)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        saved_fields = json.loads(data["text_inserter_filename_fields"])
        assert saved_fields == ["date", "vehicle_no"]

    def test_load_window_size_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.load_window_size delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        # Create settings file
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"text_inserter_window_width": "800", "text_inserter_window_height": "900"}),
            encoding="utf-8",
        )

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            result = settings.load_window_size()

        assert result == (800, 900)

    def test_save_window_size_delegates_to_settings_manager(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Settings.save_window_size delegates to settings_manager."""
        from tachograph_wizard.ui.settings import Settings

        settings_path = tmp_path / "settings.json"

        with patch(
            "tachograph_wizard.core.settings_manager._get_settings_path",
            return_value=settings_path,
        ):
            settings = Settings()
            settings.save_window_size(700, 800)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["text_inserter_window_width"] == "700"
        assert data["text_inserter_window_height"] == "800"
