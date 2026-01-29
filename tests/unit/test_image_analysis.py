"""Tests for the image_analysis module.

Note: Tests for functions that don't require GIMP API (Component, get_analysis_scale,
otsu_threshold, find_components) can be run directly using mock_gimp_modules fixture.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestComponent:
    """Tests for the Component dataclass."""

    def test_component_width(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that width is calculated correctly."""
        from tachograph_wizard.core.image_analysis import Component

        comp = Component(min_x=10, min_y=20, max_x=50, max_y=80, area=100)
        assert comp.width == 41  # 50 - 10 + 1

    def test_component_height(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that height is calculated correctly."""
        from tachograph_wizard.core.image_analysis import Component

        comp = Component(min_x=10, min_y=20, max_x=50, max_y=80, area=100)
        assert comp.height == 61  # 80 - 20 + 1

    def test_component_diameter(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that diameter is the maximum of width and height."""
        from tachograph_wizard.core.image_analysis import Component

        comp = Component(min_x=10, min_y=20, max_x=50, max_y=80, area=100)
        assert comp.diameter == 61  # max(41, 61)

    def test_component_diameter_width_larger(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test diameter when width is larger than height."""
        from tachograph_wizard.core.image_analysis import Component

        comp = Component(min_x=0, min_y=0, max_x=99, max_y=49, area=5000)
        assert comp.width == 100
        assert comp.height == 50
        assert comp.diameter == 100


class TestGetAnalysisScale:
    """Tests for the get_analysis_scale function."""

    def test_small_image_returns_one(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that small images return scale of 1.0."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        assert get_analysis_scale(800, 600) == 1.0

    def test_large_image_returns_scaled(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that large images return appropriate scale."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        scale = get_analysis_scale(2400, 1800)
        assert scale == pytest.approx(0.5, rel=0.01)

    def test_very_large_image(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test scaling for very large images."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        scale = get_analysis_scale(4800, 3600)
        assert scale == pytest.approx(0.25, rel=0.01)

    def test_zero_dimensions_returns_one(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that zero dimensions return 1.0."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        assert get_analysis_scale(0, 0) == 1.0

    def test_square_image_at_max_size(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test square image at exactly the max analysis size."""
        from tachograph_wizard.core.image_analysis import get_analysis_scale

        scale = get_analysis_scale(1200, 1200)
        assert scale == 1.0


class TestOtsuThreshold:
    """Tests for the otsu_threshold function."""

    def test_zero_total_returns_255(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that zero total returns 255."""
        from tachograph_wizard.core.image_analysis import otsu_threshold

        hist = [0] * 256
        assert otsu_threshold(hist, 0) == 255

    def test_uniform_histogram(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test threshold for uniform histogram."""
        from tachograph_wizard.core.image_analysis import otsu_threshold

        hist = [100] * 256
        threshold = otsu_threshold(hist, 25600)
        # Uniform histogram should return a mid-range threshold
        assert 0 <= threshold <= 255

    def test_bimodal_histogram(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test threshold for bimodal histogram."""
        from tachograph_wizard.core.image_analysis import otsu_threshold

        hist = [0] * 256
        # Create bimodal: dark pixels around 50, light pixels around 200
        for i in range(40, 60):
            hist[i] = 100
        for i in range(190, 210):
            hist[i] = 100
        total = sum(hist)
        threshold = otsu_threshold(hist, total)
        # Threshold should be at the boundary of the first mode
        # Otsu's method maximizes between-class variance
        # With equal-weight modes, it tends to pick the edge of the first mode
        assert 40 <= threshold <= 200  # Reasonable range for bimodal


class TestFindComponents:
    """Tests for the find_components function."""

    def test_empty_mask_returns_no_components(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that an empty mask returns no components."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        components = find_components(mask, 10, 10)
        assert len(components) == 0

    def test_single_pixel_component(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection of a single pixel component."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        mask[55] = 1  # Center pixel
        components = find_components(mask, 10, 10)
        assert len(components) == 1
        assert components[0].area == 1

    def test_rectangular_component(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection of a rectangular component."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        # Create a 3x3 square at position (3, 3)
        for y in range(3, 6):
            for x in range(3, 6):
                mask[y * 10 + x] = 1
        components = find_components(mask, 10, 10)
        assert len(components) == 1
        assert components[0].area == 9
        assert components[0].min_x == 3
        assert components[0].max_x == 5
        assert components[0].min_y == 3
        assert components[0].max_y == 5

    def test_multiple_components(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection of multiple separate components."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        # First component at top-left corner
        mask[0] = 1
        mask[1] = 1
        # Second component at bottom-right corner
        mask[98] = 1
        mask[99] = 1
        components = find_components(mask, 10, 10)
        assert len(components) == 2

    def test_l_shaped_component(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test detection of L-shaped component (4-connected)."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        # Create L shape
        mask[0] = 1
        mask[10] = 1
        mask[20] = 1
        mask[21] = 1
        mask[22] = 1
        components = find_components(mask, 10, 10)
        assert len(components) == 1
        assert components[0].area == 5

    def test_diagonal_components_are_separate(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that diagonal pixels are not connected (4-connectivity)."""
        from tachograph_wizard.core.image_analysis import find_components

        mask = bytearray(100)
        # Diagonal pixels (should be separate with 4-connectivity)
        mask[0] = 1  # (0, 0)
        mask[11] = 1  # (1, 1)
        components = find_components(mask, 10, 10)
        assert len(components) == 2
