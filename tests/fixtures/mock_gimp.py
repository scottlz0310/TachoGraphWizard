"""Mock GIMP API for testing.

Provides mock objects for GIMP, GimpUi, Gegl, and related modules
to allow testing without GIMP installation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock


class MockGimp:
    """Mock GIMP module for testing."""

    @staticmethod
    def create_mock_image(width: int = 1000, height: int = 1000) -> Mock:
        """Create a mock Gimp.Image object.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Mock image object with basic properties configured.
        """
        image = MagicMock()
        image.get_width.return_value = width
        image.get_height.return_value = height
        image.get_active_drawable.return_value = MockGimp.create_mock_drawable()
        image.get_active_layer.return_value = MockGimp.create_mock_layer()
        image.find_next_guide.return_value = None
        image.get_selected_drawables.return_value = (1, [MockGimp.create_mock_drawable()])
        return image

    @staticmethod
    def create_mock_drawable() -> Mock:
        """Create a mock Gimp.Drawable object.

        Returns:
            Mock drawable with basic properties.
        """
        drawable = MagicMock()
        drawable.has_alpha.return_value = True
        drawable.bounds.return_value = (True, 0, 0, 500, 500)
        drawable.add_alpha.return_value = None
        return drawable

    @staticmethod
    def create_mock_layer() -> Mock:
        """Create a mock Gimp.Layer object.

        Returns:
            Mock layer with basic properties.
        """
        layer = MagicMock()
        layer.has_alpha.return_value = True
        layer.bounds.return_value = (True, 0, 0, 500, 500)
        layer.add_alpha.return_value = None
        return layer

    @staticmethod
    def create_mock_guide() -> Mock:
        """Create a mock Gimp.Guide object.

        Returns:
            Mock guide object.
        """
        guide = MagicMock()
        guide.get_id.return_value = 1
        return guide

    @staticmethod
    def create_mock_color(r: float = 1.0, g: float = 1.0, b: float = 1.0) -> Mock:
        """Create a mock Gegl.Color object.

        Args:
            r: Red component (0.0-1.0).
            g: Green component (0.0-1.0).
            b: Blue component (0.0-1.0).

        Returns:
            Mock color object.
        """
        color = MagicMock()
        color.r = r
        color.g = g
        color.b = b
        return color

    @staticmethod
    def create_mock_pdb() -> Mock:
        """Create a mock PDB (Procedural Database) object.

        Returns:
            Mock PDB with common procedures.
        """
        pdb = MagicMock()

        # Mock successful procedure execution
        success_result = MagicMock()
        success_result.index.return_value = 0  # PDBStatusType.SUCCESS

        pdb.run_procedure.return_value = success_result
        return pdb

    @staticmethod
    def create_mock_value_array() -> Mock:
        """Create a mock Gimp.ValueArray.

        Returns:
            Mock ValueArray object.
        """
        value_array = MagicMock()
        value_array.index.return_value = 0
        return value_array
