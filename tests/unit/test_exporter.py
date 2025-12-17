"""Unit tests for the Exporter module."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestExporter:
    """Test Exporter class."""

    def test_generate_filename_full(self, mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock]) -> None:
        """Test filename generation with all parameters."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 1, 15),
            vehicle_number="ABC-123",
            driver_name="Taro Yamada",
        )

        assert filename == "20250115_ABC-123_TaroYamada.png"

    def test_generate_filename_partial(self, mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock]) -> None:
        """Test filename with only date."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 1, 15),
        )

        assert filename == "20250115.png"

    def test_generate_filename_with_vehicle_only(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test filename with date and vehicle number."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 12, 31),
            vehicle_number="456",
        )

        assert filename == "20251231_456.png"

    def test_generate_filename_sanitizes_spaces(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that spaces in vehicle number are replaced with underscores."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 1, 1),
            vehicle_number="ABC 123",
            driver_name="Test Driver",
        )

        assert filename == "20250101_ABC_123_TestDriver.png"

    def test_generate_filename_sanitizes_slashes(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that slashes are replaced with dashes."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 1, 1),
            vehicle_number="ABC/123",
            driver_name="Test/Driver",
        )

        assert filename == "20250101_ABC-123_Test-Driver.png"

    def test_generate_filename_default_date(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test filename generation uses today's date when not specified."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            vehicle_number="999",
        )

        # Should start with YYYYMMDD format
        assert len(filename.split("_")[0]) == 8
        assert filename.endswith("_999.png")

    def test_generate_filename_custom_extension(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test filename with custom extension."""
        from tachograph_wizard.core.exporter import Exporter

        filename = Exporter.generate_filename(
            date=date(2025, 1, 1),
            vehicle_number="123",
            extension="jpg",
        )

        assert filename == "20250101_123.jpg"

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    def test_save_png_creates_directory(
        self,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that save_png creates output directory if it doesn't exist."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        output_path = tmp_path / "subdir" / "test.png"
        mock_gimp.get_pdb.return_value = MagicMock()

        # Mock successful save
        result = MagicMock()
        result.index.return_value = 0  # SUCCESS
        mock_gimp.get_pdb.return_value.run_procedure.return_value = result

        # Execute
        try:
            Exporter.save_png(mock_image, output_path)
        except (RuntimeError, AttributeError):
            # May fail due to incomplete mocking, but directory should be created
            pass

        # Verify directory was created
        assert output_path.parent.exists()
