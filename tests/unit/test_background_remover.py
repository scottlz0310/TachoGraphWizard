# pyright: reportPrivateUsage=false
"""Unit tests for background_remover module."""

from __future__ import annotations

from unittest.mock import MagicMock


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
