# pyright: reportPrivateUsage=false
"""Extended unit tests for Exporter - covers save_png and save_with_naming_convention."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestExporterSavePng:
    """Test Exporter.save_png integration paths."""

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_flatten(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png with flatten=True calls image.flatten()."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "output" / "test.png"
        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = True
        mock_image.flatten.return_value = mock_merged

        # Make Gimp.file_save succeed
        mock_gimp.file_save = MagicMock(return_value=True)
        mock_gimp.PDBStatusType.SUCCESS = 0

        result = Exporter.save_png(mock_image, output_path, flatten=True)
        assert result is True
        mock_image.flatten.assert_called_once()

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_merge_visible(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png with flatten=False calls merge_visible_layers."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "test.png"
        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = True
        mock_image.merge_visible_layers.return_value = mock_merged

        mock_gimp.file_save = MagicMock(return_value=True)
        mock_gimp.PDBStatusType.SUCCESS = 0
        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        result = Exporter.save_png(mock_image, output_path, flatten=False)
        assert result is True
        mock_image.merge_visible_layers.assert_called_once()

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_fallback_to_pdb(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png falls back to PDB procedure when file API fails."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "test.png"
        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = True
        mock_image.merge_visible_layers.return_value = mock_merged

        # Make file APIs fail
        mock_gimp.file_save = None
        mock_gimp.file_export = None
        mock_gimp.PDBStatusType.SUCCESS = 0
        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        # PDB procedure result indicating success
        mock_result = MagicMock()
        mock_result.index.return_value = 0
        mock_run_pdb.return_value = mock_result

        result = Exporter.save_png(mock_image, output_path, flatten=False)
        assert result is True
        mock_run_pdb.assert_called()

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_no_drawables_uses_fallback(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png uses fallback drawable when get_selected_drawables returns empty."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "test.png"
        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = False
        mock_image.merge_visible_layers.return_value = mock_merged

        # get_selected_drawables returns empty
        mock_image.get_selected_drawables.return_value = (0, [])

        mock_gimp.file_save = MagicMock(return_value=True)
        mock_gimp.PDBStatusType.SUCCESS = 0
        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        result = Exporter.save_png(mock_image, output_path, flatten=False)
        assert result is True

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_raises_when_no_drawable(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png raises RuntimeError when no drawable is available."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "test.png"
        mock_image = MagicMock()
        mock_image.merge_visible_layers.return_value = None
        mock_image.get_selected_drawables.return_value = (0, [])
        mock_image.get_active_drawable.return_value = None
        mock_image.get_active_layer.return_value = None
        mock_image.get_layers.return_value = []

        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        with pytest.raises(RuntimeError, match="No drawable"):
            Exporter.save_png(mock_image, output_path)

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_png_file_export_fallback(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_png falls to file_export when file_save fails but not raises."""
        from tachograph_wizard.core.exporter import Exporter

        output_path = tmp_path / "test.png"
        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = True
        mock_image.merge_visible_layers.return_value = mock_merged

        # file_save returns False (not success), file_export returns True
        mock_gimp.file_save = MagicMock(return_value=False)
        mock_gimp.file_export = MagicMock(return_value=True)
        mock_gimp.PDBStatusType.SUCCESS = 0
        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        result = Exporter.save_png(mock_image, output_path, flatten=False)
        assert result is True


class TestExporterSaveWithNamingConvention:
    """Test Exporter.save_with_naming_convention."""

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_with_naming_convention(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_image: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_with_naming_convention generates filename and saves."""
        from tachograph_wizard.core.exporter import Exporter

        mock_merged = MagicMock()
        mock_merged.has_alpha.return_value = True
        mock_image.merge_visible_layers.return_value = mock_merged

        mock_gimp.file_save = MagicMock(return_value=True)
        mock_gimp.PDBStatusType.SUCCESS = 0
        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        result = Exporter.save_with_naming_convention(
            mock_image,
            tmp_path,
            date=date(2025, 3, 15),
            vehicle_number="ABC",
            driver_name="Taro",
        )

        assert result.name == "20250315_ABC_Taro.png"

    @patch("tachograph_wizard.core.exporter.Gimp")
    @patch("tachograph_wizard.core.exporter.Gio")
    @patch("tachograph_wizard.core.exporter.run_pdb_procedure")
    def test_save_with_naming_convention_raises_on_failure(
        self,
        mock_run_pdb: MagicMock,
        mock_gio: MagicMock,
        mock_gimp: MagicMock,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """save_with_naming_convention raises when save fails."""
        from tachograph_wizard.core.exporter import Exporter

        mock_image = MagicMock()
        mock_image.merge_visible_layers.return_value = None
        mock_image.get_selected_drawables.return_value = (0, [])
        mock_image.get_active_drawable.return_value = None
        mock_image.get_active_layer.return_value = None
        mock_image.get_layers.return_value = []

        mock_gimp.MergeType.EXPAND_AS_NECESSARY = 0

        with pytest.raises(RuntimeError):
            Exporter.save_with_naming_convention(
                mock_image,
                tmp_path,
                date=date(2025, 3, 15),
            )


import pytest
