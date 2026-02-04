# pyright: reportPrivateUsage=false
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
        except RuntimeError, AttributeError:
            # May fail due to incomplete mocking, but directory should be created
            pass

        # Verify directory was created
        assert output_path.parent.exists()

    def test_is_success_status_with_bool_true(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with boolean True."""
        from tachograph_wizard.core.exporter import Exporter

        assert Exporter._is_success_status(True) is True

    def test_is_success_status_with_bool_false(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with boolean False."""
        from tachograph_wizard.core.exporter import Exporter

        assert Exporter._is_success_status(False) is False

    def test_is_success_status_with_none(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with None."""
        from tachograph_wizard.core.exporter import Exporter

        assert Exporter._is_success_status(None) is False

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_is_success_status_with_success_int(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with SUCCESS integer."""
        from tachograph_wizard.core.exporter import Exporter

        # Set up the SUCCESS value properly
        mock_gimp.PDBStatusType.SUCCESS = 0

        # SUCCESS is 0
        assert Exporter._is_success_status(0) is True

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_is_success_status_with_failure_int(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with non-SUCCESS integer."""
        from tachograph_wizard.core.exporter import Exporter

        # Set up the SUCCESS value properly
        mock_gimp.PDBStatusType.SUCCESS = 0

        # Non-zero is failure
        assert Exporter._is_success_status(1) is False

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_is_success_status_with_tuple(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with tuple containing SUCCESS."""
        from tachograph_wizard.core.exporter import Exporter

        # Set up the SUCCESS value properly
        mock_gimp.PDBStatusType.SUCCESS = 0

        assert Exporter._is_success_status((0, "data")) is True

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_is_success_status_with_list(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with list containing SUCCESS."""
        from tachograph_wizard.core.exporter import Exporter

        # Set up the SUCCESS value properly
        mock_gimp.PDBStatusType.SUCCESS = 0

        assert Exporter._is_success_status([0, "data"]) is True

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_is_success_status_with_index_method(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _is_success_status with object having index method."""
        from tachograph_wizard.core.exporter import Exporter

        # Set up the SUCCESS value properly
        mock_gimp.PDBStatusType.SUCCESS = 0

        result = MagicMock()
        result.index.return_value = 0  # SUCCESS
        assert Exporter._is_success_status(result) is True

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_try_file_api_save_with_file_save_success(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_drawable: MagicMock,
    ) -> None:
        """Test _try_file_api_save succeeds with Gimp.file_save."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_file = MagicMock()
        mock_gimp.file_save = MagicMock(return_value=True)

        # Execute
        result = Exporter._try_file_api_save(mock_image, [mock_drawable], mock_file)

        # Verify
        assert result is True
        mock_gimp.file_save.assert_called_once()

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_try_file_api_save_with_file_export_success(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_drawable: MagicMock,
    ) -> None:
        """Test _try_file_api_save succeeds with Gimp.file_export."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_file = MagicMock()
        mock_gimp.file_save = MagicMock(side_effect=Exception("Not available"))
        mock_gimp.file_export = MagicMock(return_value=True)

        # Execute
        result = Exporter._try_file_api_save(mock_image, [mock_drawable], mock_file)

        # Verify
        assert result is True
        mock_gimp.file_export.assert_called_once()

    @patch("tachograph_wizard.core.exporter.Gimp")
    def test_try_file_api_save_with_no_api_available(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_drawable: MagicMock,
    ) -> None:
        """Test _try_file_api_save returns False when no API available."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_file = MagicMock()
        # Simulate missing save APIs
        mock_gimp.file_save = None
        mock_gimp.file_export = None

        # Execute
        result = Exporter._try_file_api_save(mock_image, [mock_drawable], mock_file)

        # Verify
        assert result is False

    def test_get_fallback_drawable_with_active_drawable(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_drawable: MagicMock,
    ) -> None:
        """Test _get_fallback_drawable returns active drawable."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_image.get_active_drawable.return_value = mock_drawable

        # Execute
        result = Exporter._get_fallback_drawable(mock_image)

        # Verify
        assert result == mock_drawable

    def test_get_fallback_drawable_with_active_layer(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_layer: MagicMock,
    ) -> None:
        """Test _get_fallback_drawable returns active layer when no active drawable."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_image.get_active_drawable.return_value = None
        mock_image.get_active_layer.return_value = mock_layer

        # Execute
        result = Exporter._get_fallback_drawable(mock_image)

        # Verify
        assert result == mock_layer

    def test_get_fallback_drawable_with_get_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        mock_layer: MagicMock,
    ) -> None:
        """Test _get_fallback_drawable uses get_layers as last resort."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_image.get_active_drawable.return_value = None
        mock_image.get_active_layer.return_value = None
        mock_image.get_layers.return_value = [mock_layer]

        # Execute
        result = Exporter._get_fallback_drawable(mock_image)

        # Verify
        assert result == mock_layer

    def test_get_fallback_drawable_returns_none(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
    ) -> None:
        """Test _get_fallback_drawable returns None when no drawable available."""
        from tachograph_wizard.core.exporter import Exporter

        # Setup
        mock_image.get_active_drawable.return_value = None
        mock_image.get_active_layer.return_value = None
        mock_image.get_layers.return_value = []

        # Execute
        result = Exporter._get_fallback_drawable(mock_image)

        # Verify
        assert result is None
