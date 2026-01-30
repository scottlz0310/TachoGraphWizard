# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
"""Unit tests for image_cleanup module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestDespeckle:
    """Test despeckle function."""

    def test_despeckle_tries_plug_in_despeckle_first(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test despeckle tries plug-in-despeckle first."""
        from tachograph_wizard.core.image_cleanup import despeckle

        mock_drawable = MagicMock()
        mock_image = MagicMock()
        mock_drawable.get_image.return_value = mock_image

        with patch("tachograph_wizard.core.image_cleanup.run_pdb_procedure") as mock_pdb:
            mock_result = MagicMock()
            mock_result.index.return_value = 0  # Gimp.PDBStatusType.SUCCESS
            mock_pdb.return_value = mock_result

            despeckle(mock_drawable, radius=3)

            # Verify plug-in-despeckle was called (should be the first call)
            assert mock_pdb.call_count >= 1
            first_call_args = mock_pdb.call_args_list[0]
            assert first_call_args[0][0] == "plug-in-despeckle"

    def test_despeckle_falls_back_to_median_noise(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test despeckle falls back to median-noise if despeckle fails."""
        from tachograph_wizard.core.image_cleanup import despeckle

        mock_drawable = MagicMock()
        mock_image = MagicMock()
        mock_drawable.get_image.return_value = mock_image

        def mock_pdb_side_effect(name: str, *args, **kwargs):  # noqa: ARG001
            if name == "plug-in-despeckle":
                msg = "despeckle failed"
                raise RuntimeError(msg)
            # For plug-in-median-noise, return success
            result = MagicMock()
            result.index.return_value = 0
            return result

        with patch(
            "tachograph_wizard.core.image_cleanup.run_pdb_procedure",
            side_effect=mock_pdb_side_effect,
        ) as mock_pdb:
            despeckle(mock_drawable, radius=3)

            # Should have tried both methods
            assert mock_pdb.call_count == 2
            assert mock_pdb.call_args_list[0][0][0] == "plug-in-despeckle"
            assert mock_pdb.call_args_list[1][0][0] == "plug-in-median-noise"

    def test_despeckle_handles_all_failures_gracefully(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test despeckle handles all failures gracefully."""
        from tachograph_wizard.core.image_cleanup import despeckle

        mock_drawable = MagicMock()
        mock_image = MagicMock()
        mock_drawable.get_image.return_value = mock_image

        with patch(
            "tachograph_wizard.core.image_cleanup.run_pdb_procedure",
            side_effect=RuntimeError("all methods fail"),
        ):
            # Should not raise, just log and continue
            despeckle(mock_drawable, radius=3)


class TestAutoCleanupAndCrop:
    """Test auto_cleanup_and_crop function."""

    def test_auto_cleanup_adds_alpha_if_needed(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto_cleanup_and_crop adds alpha channel if needed."""
        from tachograph_wizard.core.image_cleanup import auto_cleanup_and_crop

        _gimp_mock, _, _ = mock_gimp_modules

        mock_image = MagicMock()
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 80
        mock_image.select_ellipse = MagicMock()

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = False

        auto_cleanup_and_crop(mock_drawable, ellipse_padding=10)

        # Should add alpha channel
        mock_drawable.add_alpha.assert_called_once()

    def test_auto_cleanup_creates_ellipse_selection(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto_cleanup_and_crop creates correct ellipse selection."""
        from tachograph_wizard.core.image_cleanup import auto_cleanup_and_crop

        _gimp_mock, _, _ = mock_gimp_modules

        mock_image = MagicMock()
        mock_image.get_width.return_value = 200
        mock_image.get_height.return_value = 150
        mock_image.select_ellipse = MagicMock()

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True

        auto_cleanup_and_crop(mock_drawable, ellipse_padding=20)

        # Verify ellipse selection with correct parameters
        # x=20, y=20, width=160 (200-40), height=110 (150-40)
        mock_image.select_ellipse.assert_called_once()
        args = mock_image.select_ellipse.call_args.args
        assert args[1] == 20  # x
        assert args[2] == 20  # y
        assert args[3] == 160  # width
        assert args[4] == 110  # height

    def test_auto_cleanup_handles_small_images(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test auto_cleanup_and_crop handles small images correctly."""
        from tachograph_wizard.core.image_cleanup import auto_cleanup_and_crop

        _gimp_mock, _, _ = mock_gimp_modules

        mock_image = MagicMock()
        mock_image.get_width.return_value = 10
        mock_image.get_height.return_value = 10
        mock_image.select_ellipse = MagicMock()

        mock_drawable = MagicMock()
        mock_drawable.get_image.return_value = mock_image
        mock_drawable.has_alpha.return_value = True

        auto_cleanup_and_crop(mock_drawable, ellipse_padding=5)

        # Should create ellipse with minimum size of 1
        args = mock_image.select_ellipse.call_args.args
        assert args[3] >= 1  # width >= 1
        assert args[4] >= 1  # height >= 1


class TestAddCenterGuides:
    """Test add_center_guides function."""

    def test_add_center_guides_calculates_correct_positions(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides calculates center positions correctly."""
        from tachograph_wizard.core.image_cleanup import add_center_guides

        mock_image = MagicMock()
        mock_image.get_width.return_value = 400
        mock_image.get_height.return_value = 300

        add_center_guides(mock_image)

        # Should add guides at 50% positions
        mock_image.add_vguide.assert_called_once_with(200)  # 400 // 2
        mock_image.add_hguide.assert_called_once_with(150)  # 300 // 2

    def test_add_center_guides_handles_vguide_failure(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides continues if vguide fails."""
        from tachograph_wizard.core.image_cleanup import add_center_guides

        mock_image = MagicMock()
        mock_image.get_width.return_value = 400
        mock_image.get_height.return_value = 300
        mock_image.add_vguide.side_effect = Exception("vguide failed")

        # Should not raise
        add_center_guides(mock_image)

        # Should still attempt hguide
        mock_image.add_hguide.assert_called_once_with(150)

    def test_add_center_guides_handles_hguide_failure(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test add_center_guides continues if hguide fails."""
        from tachograph_wizard.core.image_cleanup import add_center_guides

        mock_image = MagicMock()
        mock_image.get_width.return_value = 400
        mock_image.get_height.return_value = 300
        mock_image.add_hguide.side_effect = Exception("hguide failed")

        # Should not raise
        add_center_guides(mock_image)

        # Should have attempted vguide
        mock_image.add_vguide.assert_called_once_with(200)
