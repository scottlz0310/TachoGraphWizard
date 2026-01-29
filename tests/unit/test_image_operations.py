"""Tests for the image_operations module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestDuplicateImage:
    """Tests for the duplicate_image function."""

    def test_duplicate_image_uses_method_when_available(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that image.duplicate() is used when available."""
        from tachograph_wizard.core.image_operations import duplicate_image

        mock_image = MagicMock()
        mock_dup = MagicMock()
        mock_image.duplicate.return_value = mock_dup

        result = duplicate_image(mock_image)
        assert result is mock_dup
        mock_image.duplicate.assert_called_once()

    def test_duplicate_image_falls_back_to_pdb(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that PDB is used when duplicate method is not available."""
        from tachograph_wizard.core.image_operations import duplicate_image

        mock_image = MagicMock()
        # Make duplicate method non-callable
        mock_image.duplicate = None

        mock_result = MagicMock()
        mock_dup = MagicMock()
        mock_result.index.return_value = mock_dup

        with patch("tachograph_wizard.core.image_operations.run_pdb_procedure", return_value=mock_result):
            result = duplicate_image(mock_image)
            assert result is mock_dup

    def test_duplicate_image_uses_custom_debug_log(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that custom debug_log is passed to PDB runner."""
        from tachograph_wizard.core.image_operations import duplicate_image

        mock_image = MagicMock()
        mock_image.duplicate = None  # Force PDB fallback

        mock_result = MagicMock()
        mock_result.index.return_value = MagicMock()
        custom_log = MagicMock()

        with patch(
            "tachograph_wizard.core.image_operations.run_pdb_procedure",
            return_value=mock_result,
        ) as mock_pdb:
            duplicate_image(mock_image, debug_log=custom_log)
            mock_pdb.assert_called_once()
            # Check that debug_log was passed
            call_kwargs = mock_pdb.call_args.kwargs
            assert call_kwargs.get("debug_log") is custom_log


class TestCropImage:
    """Tests for the crop_image function."""

    def test_crop_image_uses_method_when_available(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that image.crop() is used when available."""
        from tachograph_wizard.core.image_operations import crop_image

        mock_image = MagicMock()

        crop_image(mock_image, 10, 20, 100, 200)
        mock_image.crop.assert_called_once_with(100, 200, 10, 20)

    def test_crop_image_falls_back_to_pdb(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that PDB is used when crop method is not available."""
        from tachograph_wizard.core.image_operations import crop_image

        mock_image = MagicMock()
        mock_image.crop = None  # Make crop method non-callable

        with patch("tachograph_wizard.core.image_operations.run_pdb_procedure") as mock_pdb:
            crop_image(mock_image, 10, 20, 100, 200)
            mock_pdb.assert_called_once()


class TestApplyComponentMask:
    """Tests for the apply_component_mask function."""

    def test_apply_component_mask_calls_pdb_procedures(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that PDB procedures are called for component mask."""
        from tachograph_wizard.core.image_operations import apply_component_mask

        mock_image = MagicMock()
        mock_layer = MagicMock()
        mock_layer.has_alpha.return_value = True
        mock_image.get_layers.return_value = [mock_layer]
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        # Create a simple mask with one component pixel
        comp_mask = bytearray(100)
        comp_mask[55] = 1  # Single pixel at (5, 5)

        # Mock is_empty to return False (has selection)
        mock_empty_result = MagicMock()
        mock_empty_result.index.return_value = False

        with patch(
            "tachograph_wizard.core.image_operations.run_pdb_procedure",
            return_value=mock_empty_result,
        ) as mock_pdb:
            apply_component_mask(
                mock_image,
                comp_mask,
                mask_width=10,
                mask_height=10,
                crop_x=0,
                crop_y=0,
                scale_x=0.1,
                scale_y=0.1,
                threshold=128,
            )
            # Should call multiple PDB procedures
            assert mock_pdb.call_count >= 1

    def test_apply_component_mask_adds_alpha_when_missing(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that alpha channel is added when missing."""
        from tachograph_wizard.core.image_operations import apply_component_mask

        mock_image = MagicMock()
        mock_layer = MagicMock()
        mock_layer.has_alpha.return_value = False
        mock_image.get_layers.return_value = [mock_layer]
        mock_image.get_width.return_value = 100
        mock_image.get_height.return_value = 100

        comp_mask = bytearray(100)
        comp_mask[55] = 1

        mock_empty_result = MagicMock()
        mock_empty_result.index.return_value = True  # Empty selection

        with patch(
            "tachograph_wizard.core.image_operations.run_pdb_procedure",
            return_value=mock_empty_result,
        ):
            apply_component_mask(
                mock_image,
                comp_mask,
                mask_width=10,
                mask_height=10,
                crop_x=0,
                crop_y=0,
                scale_x=0.1,
                scale_y=0.1,
                threshold=128,
            )
            mock_layer.add_alpha.assert_called_once()

    def test_apply_component_mask_handles_no_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that function returns early when no layers exist."""
        from tachograph_wizard.core.image_operations import apply_component_mask

        mock_image = MagicMock()
        mock_image.get_layers.return_value = []

        comp_mask = bytearray(100)

        # Should not raise, just return
        apply_component_mask(
            mock_image,
            comp_mask,
            mask_width=10,
            mask_height=10,
            crop_x=0,
            crop_y=0,
            scale_x=0.1,
            scale_y=0.1,
            threshold=128,
        )

    def test_apply_component_mask_handles_exception(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that exceptions are caught and logged."""
        from tachograph_wizard.core.image_operations import apply_component_mask

        mock_image = MagicMock()
        mock_image.get_layers.side_effect = Exception("Test error")

        comp_mask = bytearray(100)
        mock_log = MagicMock()

        # Should not raise, should log error
        apply_component_mask(
            mock_image,
            comp_mask,
            mask_width=10,
            mask_height=10,
            crop_x=0,
            crop_y=0,
            scale_x=0.1,
            scale_y=0.1,
            threshold=128,
            debug_log=mock_log,
        )
        # Verify that debug_log was called with error message
        mock_log.assert_called()
        call_args = mock_log.call_args[0][0]
        assert "failed" in call_args.lower() or "error" in call_args.lower()
