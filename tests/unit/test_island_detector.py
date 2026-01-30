# pyright: reportPrivateUsage=false
# pyright: reportUnknownLambdaType=false
# pyright: reportMissingParameterType=false
"""Unit tests for island_detector module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestRemoveGarbageKeepLargestIsland:
    """Test remove_garbage_keep_largest_island function."""

    def test_adds_alpha_channel_if_needed(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that alpha channel is added if not present."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = False
        mock_drawable.copy.return_value = MagicMock()

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure"),
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b""),
        ):
            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Should add alpha channel
        mock_drawable.add_alpha.assert_called_once()

    def test_creates_working_layer_copy(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that a working layer copy is created."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        mock_work_layer = MagicMock()
        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure"),
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b""),
        ):
            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Should create a copy
        mock_drawable.copy.assert_called_once()
        # Should insert the work layer
        mock_image.insert_layer.assert_called_once_with(mock_work_layer, None, 0)

    def test_removes_working_layer_after_processing(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that working layer is removed after processing."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        mock_work_layer = MagicMock()
        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure") as mock_pdb,
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b"test"),
        ):
            # Mock selection check to return empty
            def pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
                if name == "gimp-selection-is-empty":
                    result = MagicMock()
                    result.index.return_value = True  # Empty selection
                    return result
                return MagicMock()

            mock_pdb.side_effect = pdb_side_effect

            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Should remove the working layer
        mock_image.remove_layer.assert_called_once_with(mock_work_layer)

    def test_handles_color_selection_failure_gracefully(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test handling when color selection fails."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        mock_work_layer = MagicMock()
        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        def pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
            if name == "gimp-image-select-color":
                msg = "selection failed"
                raise RuntimeError(msg)
            if name == "gimp-image-select-contiguous-color":
                msg = "selection failed"
                raise RuntimeError(msg)
            if name == "gimp-selection-is-empty":
                result = MagicMock()
                result.index.return_value = True
                return result
            return MagicMock()

        with (
            patch(
                "tachograph_wizard.core.island_detector.run_pdb_procedure",
                side_effect=pdb_side_effect,
            ),
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b""),
        ):
            # Should not raise
            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Should still remove working layer
        mock_image.remove_layer.assert_called_once_with(mock_work_layer)

    def test_applies_threshold_correctly(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test threshold calculation and application."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        mock_work_layer = MagicMock()
        mock_buffer = MagicMock()
        mock_work_layer.get_buffer.return_value = mock_buffer

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure") as mock_pdb,
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b""),
        ):

            def pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
                if name == "gimp-selection-is-empty":
                    result = MagicMock()
                    result.index.return_value = True
                    return result
                return MagicMock()

            mock_pdb.side_effect = pdb_side_effect

            # Test with threshold=15.0
            # Expected: lower_threshold = max(0, 255 - 15*2) = 225
            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Verify desaturate was called
        calls = [call[0][0] for call in mock_pdb.call_args_list]
        assert "gimp-drawable-desaturate" in calls

    def test_creates_ellipse_intersection(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that ellipse selection is created for intersection."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 200
        mock_image.get_height.return_value = 200

        mock_work_layer = MagicMock()
        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure") as mock_pdb,
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b""),
        ):

            def pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
                if name == "gimp-selection-is-empty":
                    result = MagicMock()
                    result.index.return_value = True
                    return result
                return MagicMock()

            mock_pdb.side_effect = pdb_side_effect

            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Verify ellipse selection was called
        calls = [call[0][0] for call in mock_pdb.call_args_list]
        assert "gimp-image-select-ellipse" in calls

    def test_applies_shrink_and_grow_to_selection(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that selection is shrunk and grown to remove noise."""
        from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island

        mock_image = MagicMock()
        mock_image.get_width.return_value = 200
        mock_image.get_height.return_value = 200

        mock_work_layer = MagicMock()
        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True
        mock_drawable.copy.return_value = mock_work_layer

        with (
            patch("tachograph_wizard.core.island_detector.run_pdb_procedure") as mock_pdb,
            patch("tachograph_wizard.core.island_detector.buffer_get_bytes", return_value=b"test"),
        ):

            def pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
                if name == "gimp-selection-is-empty":
                    result = MagicMock()
                    result.index.return_value = False  # Not empty
                    return result
                if name == "gimp-selection-bounds":
                    result = MagicMock()
                    result.index.side_effect = lambda idx: True if idx == 1 else 10
                    return result
                return MagicMock()

            mock_pdb.side_effect = pdb_side_effect

            remove_garbage_keep_largest_island(mock_drawable, threshold=15.0)

        # Verify shrink and grow were called
        calls = [call[0][0] for call in mock_pdb.call_args_list]
        assert "gimp-selection-shrink" in calls
        assert "gimp-selection-grow" in calls
