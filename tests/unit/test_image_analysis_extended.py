# pyright: reportPrivateUsage=false
"""Extended unit tests for image_analysis - covers missing branches."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestGetImageDpi:
    """Test get_image_dpi function."""

    def test_valid_dpi(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns DPI when resolution is valid."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = (300.0, 300.0)

        result = get_image_dpi(image)
        assert result == 300.0

    def test_dpi_out_of_range_low(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when DPI is below 50."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = (10.0, 10.0)

        result = get_image_dpi(image)
        assert result is None

    def test_dpi_out_of_range_high(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when DPI exceeds 1200."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = (2000.0, 2000.0)

        result = get_image_dpi(image)
        assert result is None

    def test_dpi_get_resolution_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when get_resolution raises."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.side_effect = Exception("fail")

        result = get_image_dpi(image)
        assert result is None

    def test_dpi_invalid_resolution_format(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when resolution is not a tuple/list."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = "invalid"

        result = get_image_dpi(image)
        assert result is None

    def test_dpi_uses_y_res(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Uses y_res when y_res > 0."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = (150.0, 300.0)

        result = get_image_dpi(image)
        assert result == 300.0

    def test_dpi_uses_x_res_when_y_zero(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Falls back to x_res when y_res is 0."""
        from tachograph_wizard.core.image_analysis import get_image_dpi

        image = MagicMock()
        image.get_resolution.return_value = (150.0, 0.0)

        result = get_image_dpi(image)
        assert result == 150.0


class TestGetAnalysisDrawable:
    """Test get_analysis_drawable function."""

    def test_returns_active_drawable(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns active drawable when available."""
        from tachograph_wizard.core.image_analysis import get_analysis_drawable

        image = MagicMock()
        drawable = MagicMock()
        image.get_active_drawable.return_value = drawable

        result = get_analysis_drawable(image)
        assert result is drawable

    def test_fallback_to_first_layer(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Falls back to first layer when no active drawable."""
        from tachograph_wizard.core.image_analysis import get_analysis_drawable

        image = MagicMock()
        image.get_active_drawable.return_value = None
        layer = MagicMock()
        image.get_layers.return_value = [layer]

        result = get_analysis_drawable(image)
        assert result is layer

    def test_raises_when_no_layers(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises RuntimeError when no layers available."""
        from tachograph_wizard.core.image_analysis import get_analysis_drawable

        image = MagicMock()
        image.get_active_drawable.return_value = None
        image.get_layers.return_value = []

        with pytest.raises(RuntimeError, match="No layers"):
            get_analysis_drawable(image)

    def test_fallback_when_get_active_drawable_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Falls back when get_active_drawable raises."""
        from tachograph_wizard.core.image_analysis import get_analysis_drawable

        image = MagicMock()
        image.get_active_drawable.side_effect = Exception("fail")
        layer = MagicMock()
        image.get_layers.return_value = [layer]

        result = get_analysis_drawable(image)
        assert result is layer


class TestFindComponentsEdgeCases:
    """Test find_components edge cases."""

    def test_single_pixel_component(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Detects single pixel as component."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray([0, 0, 0, 1, 0, 0, 0, 0, 0])
        components = find_components(mask, 3, 3)
        assert len(components) == 1
        assert components[0].area == 1

    def test_multiple_components(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Detects multiple separate components."""
        from tachograph_wizard.core.image_analysis import find_components

        # Two separate pixels
        mask = bytearray([1, 0, 0, 0, 0, 0, 0, 0, 1])
        components = find_components(mask, 3, 3)
        assert len(components) == 2

    def test_l_shaped_component(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Detects L-shaped connected component."""
        from tachograph_wizard.core.image_analysis import find_components

        # L-shape: top-left and bottom-left
        mask = bytearray(
            [
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                1,
                0,
            ]
        )
        components = find_components(mask, 3, 3)
        assert len(components) == 1
        assert components[0].area == 4

    def test_all_zeros(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Empty mask returns no components."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(9)
        components = find_components(mask, 3, 3)
        assert len(components) == 0

    def test_invalid_width(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises ValueError for non-positive width."""
        from tachograph_wizard.core.image_analysis import find_components

        with pytest.raises(ValueError, match="width must be positive"):
            find_components(bytearray(0), 0, 1)

    def test_invalid_height(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises ValueError for non-positive height."""
        from tachograph_wizard.core.image_analysis import find_components

        with pytest.raises(ValueError, match="height must be positive"):
            find_components(bytearray(0), 1, 0)

    def test_mask_length_mismatch(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises ValueError when mask length doesn't match dimensions."""
        from tachograph_wizard.core.image_analysis import find_components

        with pytest.raises(ValueError, match="mask length"):
            find_components(bytearray(5), 3, 3)


class TestGetAnalysisScale:
    """Test get_analysis_scale function."""

    def test_small_image(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Small image returns scale 1.0."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        assert get_analysis_scale(100, 100) == 1.0

    def test_large_image(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Large image returns reduced scale."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        scale = get_analysis_scale(2400, 2400)
        assert scale < 1.0
        assert scale == 1200 / 2400

    def test_zero_dimensions(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Zero dimensions return scale 1.0."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        assert get_analysis_scale(0, 0) == 1.0


class TestComponentProperties:
    """Test Component dataclass properties."""

    def test_component_width(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Component width calculation."""
        from tachograph_wizard.core.image_analysis import Component

        c = Component(min_x=10, min_y=20, max_x=50, max_y=80, area=100)
        assert c.width == 41

    def test_component_height(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Component height calculation."""
        from tachograph_wizard.core.image_analysis import Component

        c = Component(min_x=10, min_y=20, max_x=50, max_y=80, area=100)
        assert c.height == 61

    def test_component_diameter(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Component diameter is max of width and height."""
        from tachograph_wizard.core.image_analysis import Component

        c = Component(min_x=0, min_y=0, max_x=100, max_y=50, area=100)
        assert c.diameter == 101  # width=101 > height=51


class TestOtsuThreshold:
    """Test otsu_threshold function."""

    def test_zero_total(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns 255 when total is zero."""
        from tachograph_wizard.core.image_analysis import otsu_threshold

        hist = [0] * 256
        assert otsu_threshold(hist, 0) == 255

    def test_bimodal_distribution(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Finds threshold between two peaks."""
        from tachograph_wizard.core.image_analysis import otsu_threshold

        hist = [0] * 256
        # Two clear peaks
        for i in range(50, 70):
            hist[i] = 100
        for i in range(180, 200):
            hist[i] = 100

        total = sum(hist)
        threshold = otsu_threshold(hist, total)
        # Should be near the boundary between the two peaks
        # Otsu maximizes between-class variance, result is at the edge of first peak
        assert 50 <= threshold <= 180


class TestBufferGetBytes:
    """Test buffer_get_bytes function."""

    def test_buffer_get_bytes_success(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """buffer_get_bytes returns bytes on success."""
        from tachograph_wizard.core.image_analysis import buffer_get_bytes

        buffer = MagicMock()
        rect = MagicMock()
        buffer.get.return_value = b"\x00\x01\x02"

        result = buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")
        assert result == b"\x00\x01\x02"

    def test_buffer_get_bytes_all_fail(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """buffer_get_bytes raises when all attempts fail."""
        from tachograph_wizard.core.image_analysis import buffer_get_bytes

        buffer = MagicMock()
        rect = MagicMock()
        buffer.get.side_effect = Exception("fail")

        with pytest.raises(RuntimeError, match="Failed to read buffer data"):
            buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")

    def test_buffer_get_bytes_with_get_data(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """buffer_get_bytes handles object with get_data method."""
        from tachograph_wizard.core.image_analysis import buffer_get_bytes

        buffer = MagicMock()
        rect = MagicMock()

        data_obj = MagicMock()
        data_obj.get_data.return_value = b"\x03\x04\x05"
        # Make it not bytes/bytearray so it falls to get_data path
        buffer.get.return_value = data_obj

        result = buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")
        assert result == b"\x03\x04\x05"
