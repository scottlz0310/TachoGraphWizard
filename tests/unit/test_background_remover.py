# pyright: reportPrivateUsage=false
"""Unit tests for background_remover module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestBackgroundRemoverAddCenterGuides:
    """Test BackgroundRemover add_center_guides method."""

    def test_add_center_guides_at_50_percent(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides adds guides at 50% positions."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image with known dimensions
        mock_image = MagicMock()
        mock_image.get_width.return_value = 1000
        mock_image.get_height.return_value = 800

        # Call add_center_guides
        BackgroundRemover.add_center_guides(mock_image)

        # Verify vertical guide at 50% width (500px)
        mock_image.add_vguide.assert_called_once_with(500)

        # Verify horizontal guide at 50% height (400px)
        mock_image.add_hguide.assert_called_once_with(400)

    def test_add_center_guides_with_odd_dimensions(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides handles odd dimensions correctly."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image with odd dimensions
        mock_image = MagicMock()
        mock_image.get_width.return_value = 999
        mock_image.get_height.return_value = 701

        # Call add_center_guides
        BackgroundRemover.add_center_guides(mock_image)

        # Verify guides at integer division results
        mock_image.add_vguide.assert_called_once_with(499)  # 999 // 2
        mock_image.add_hguide.assert_called_once_with(350)  # 701 // 2

    def test_add_center_guides_handles_vguide_exception(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides handles exception when adding vertical guide."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image
        mock_image = MagicMock()
        mock_image.get_width.return_value = 1000
        mock_image.get_height.return_value = 800
        mock_image.add_vguide.side_effect = Exception("GIMP error")

        # Should not raise, should handle gracefully
        BackgroundRemover.add_center_guides(mock_image)

        # Verify horizontal guide was still attempted
        mock_image.add_hguide.assert_called_once_with(400)

    def test_add_center_guides_handles_hguide_exception(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides handles exception when adding horizontal guide."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image
        mock_image = MagicMock()
        mock_image.get_width.return_value = 1000
        mock_image.get_height.return_value = 800
        mock_image.add_hguide.side_effect = Exception("GIMP error")

        # Should not raise, should handle gracefully
        BackgroundRemover.add_center_guides(mock_image)

        # Verify vertical guide was still added
        mock_image.add_vguide.assert_called_once_with(500)

    def test_add_center_guides_with_small_image(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides works with very small images."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image with small dimensions
        mock_image = MagicMock()
        mock_image.get_width.return_value = 10
        mock_image.get_height.return_value = 10

        # Call add_center_guides
        BackgroundRemover.add_center_guides(mock_image)

        # Verify guides at center
        mock_image.add_vguide.assert_called_once_with(5)
        mock_image.add_hguide.assert_called_once_with(5)


class TestBackgroundRemoverProcessBackgroundGuides:
    """Test BackgroundRemover process_background adds guides."""

    def test_process_background_calls_add_center_guides(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test process_background adds center guides after cleanup."""
        from unittest.mock import patch

        from tachograph_wizard.core.background_remover import BackgroundRemover

        # Create mock image and drawable
        mock_image = MagicMock()
        mock_image.get_width.return_value = 1000
        mock_image.get_height.return_value = 1000

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True

        # Mock auto_cleanup_and_crop to avoid complex setup
        with patch.object(BackgroundRemover, "auto_cleanup_and_crop"):
            # Call process_background
            BackgroundRemover.process_background(mock_drawable)

        # Verify guides were added
        mock_image.add_vguide.assert_called_once_with(500)
        mock_image.add_hguide.assert_called_once_with(500)


class TestBackgroundRemoverDelegates:
    """Test BackgroundRemover delegates to refactored modules."""

    def test_despeckle_delegates(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test despeckle delegates to image_cleanup."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        mock_drawable = MagicMock()
        with patch("tachograph_wizard.core.background_remover.despeckle") as mock_despeckle:
            BackgroundRemover.despeckle(mock_drawable, radius=5)

        mock_despeckle.assert_called_once_with(mock_drawable, radius=5)

    def test_auto_cleanup_and_crop_delegates(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto_cleanup_and_crop delegates to image_cleanup."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        mock_drawable = MagicMock()
        with patch("tachograph_wizard.core.background_remover.auto_cleanup_and_crop") as mock_cleanup:
            BackgroundRemover.auto_cleanup_and_crop(mock_drawable, ellipse_padding=12)

        mock_cleanup.assert_called_once_with(mock_drawable, ellipse_padding=12)

    def test_remove_garbage_keep_largest_island_delegates(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test remove_garbage_keep_largest_island delegates to island_detector."""
        from tachograph_wizard.core.background_remover import BackgroundRemover

        mock_drawable = MagicMock()
        with patch(
            "tachograph_wizard.core.background_remover.remove_garbage_keep_largest_island",
        ) as mock_remove:
            BackgroundRemover.remove_garbage_keep_largest_island(mock_drawable, threshold=22.5)

        mock_remove.assert_called_once_with(mock_drawable, threshold=22.5)


class TestImageCleanupModule:
    """Test image_cleanup module entrypoints."""

    def test_auto_cleanup_adds_alpha_and_crops(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto_cleanup_and_crop performs basic selection flow."""
        from tachograph_wizard.core.image_cleanup import auto_cleanup_and_crop

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 80
        mock_image.select_ellipse = MagicMock()
        mock_image.autocrop = MagicMock()

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = False

        auto_cleanup_and_crop(mock_drawable, ellipse_padding=10)

        mock_drawable.add_alpha.assert_called_once()
        args = mock_image.select_ellipse.call_args.args
        assert args[1:] == (10, 10, 80, 60)
        mock_image.autocrop.assert_called_once()

    def test_add_center_guides_invokes_guides(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides calls vguide/hguide."""
        from tachograph_wizard.core.image_cleanup import add_center_guides

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 50

        add_center_guides(mock_image)

        mock_image.add_vguide.assert_called_once_with(50)
        mock_image.add_hguide.assert_called_once_with(25)


class TestIslandDetectorModule:
    """Test island_detector module fallback behavior."""

    def test_remove_garbage_keep_largest_island_removes_layer_on_failure(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test island_detector removes work layer when selection fails."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        _gimp_mock, _, _gegl_mock = mock_gimp_modules

        mock_image = MagicMock()
        mock_image.get_width.return_value = 10
        mock_image.get_height.return_value = 10

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = MagicMock()

        def fake_run_pdb_procedure(
            name: str,
            _args: list[MagicMock],
            *,
            debug_log: MagicMock | None = None,
        ) -> MagicMock:
            _ = debug_log
            if name == "gimp-image-select-color":
                msg = "fail"
                raise RuntimeError(msg)
            if name == "gimp-image-select-contiguous-color":
                msg = "fail"
                raise RuntimeError(msg)
            if name == "gimp-selection-is-empty":
                result = MagicMock()

                def side_effect(idx: int) -> bool | None:
                    return True if idx == 1 else None

                result.index.side_effect = side_effect
                return result
            return MagicMock()

        with (
            patch(
                "tachograph_wizard.core.island_detector.run_pdb_procedure",
                side_effect=fake_run_pdb_procedure,
            ),
            patch(
                "tachograph_wizard.core.island_detector.buffer_get_bytes",
                return_value=b"",
            ),
        ):
            remove_garbage_keep_largest_island(mock_drawable, threshold=10.0)

        mock_image.remove_layer.assert_called_once_with(mock_drawable.copy.return_value)


class TestLoggingUtil:
    """Test logging_util debug_log behavior."""

    def test_debug_log_writes_log_line(self, tmp_path: Path) -> None:
        """Test debug_log writes expected line to file."""
        from tachograph_wizard.core.logging_util import debug_log

        with patch.dict(os.environ, {"TEMP": str(tmp_path)}):
            debug_log("hello", module="test_module")

        log_path = tmp_path / "tachograph_wizard.log"
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "test_module: hello" in content

    def test_debug_log_no_env_returns(self, tmp_path: Path) -> None:
        """Test debug_log returns without env variables."""
        from tachograph_wizard.core.logging_util import debug_log

        env_patch = {"TEMP": "", "TMP": "", "LOCALAPPDATA": ""}
        with patch.dict(os.environ, env_patch, clear=True):
            debug_log("hello", module="test_module")

        assert not (tmp_path / "tachograph_wizard.log").exists()

    def test_debug_log_appends(self, tmp_path: Path) -> None:
        """Test debug_log appends to existing file."""
        from tachograph_wizard.core.logging_util import debug_log

        log_path = tmp_path / "tachograph_wizard.log"
        log_path.write_text("seed\n", encoding="utf-8")

        with patch.dict(os.environ, {"TEMP": str(tmp_path)}):
            debug_log("next", module="test_module")

        content = log_path.read_text(encoding="utf-8")
        assert "seed" in content
        assert "test_module: next" in content

    def test_debug_log_handles_open_failure(self, tmp_path: Path) -> None:
        """Test debug_log gracefully handles open failures."""
        from tachograph_wizard.core import logging_util

        with (
            patch.dict(os.environ, {"TEMP": str(tmp_path)}),
            patch.object(
                logging_util.Path,
                "open",
                side_effect=OSError("fail"),
            ),
        ):
            logging_util.debug_log("hello", module="test_module")
