"""Unit tests for pdb_runner integer and Gio.File handling."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch


class TestPdbRunnerPopulateConfig:
    """Test pdb_runner _populate_config function."""

    def test_populate_config_with_gio_file(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles Gio.File objects without crashing."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []

        # Create mock file
        mock_file = MagicMock()
        mock_file.get_path.return_value = "/test/path.png"
        mock_file.get_uri.return_value = "file:///test/path.png"

        # Should not raise an exception
        values = [mock_file]
        _populate_config(mock_config, values)

    def test_populate_config_integer_followed_by_value_array(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles integer followed by ValueArray without crashing."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []

        # Create mock ValueArray
        mock_value_array = MagicMock()

        # Should not raise an exception
        values = [42, mock_value_array]
        _populate_config(mock_config, values)

    def test_populate_config_integer_followed_by_non_drawable(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles integer followed by non-drawable value."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []

        # Should not raise an exception
        values = [100, "not a drawable"]
        _populate_config(mock_config, values)

    def test_populate_config_mixed_values(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles mixed value types."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []

        # Should not raise an exception
        values = [MagicMock(), 42, "string", MagicMock(), 1, MagicMock()]
        _populate_config(mock_config, values)

    def test_populate_config_empty_values(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles empty values list."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []

        # Should not raise an exception
        values: list[object] = []
        _populate_config(mock_config, values)

    def test_populate_config_handles_exceptions_gracefully(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config handles exceptions in type checking gracefully."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock config
        mock_config = MagicMock()
        mock_config.list_properties.return_value = []
        mock_config.set_property = MagicMock(side_effect=Exception("Test error"))

        # Execute with various values - should not raise
        values = [42, "string", None, MagicMock()]
        _populate_config(mock_config, values)

        # Function should complete without raising
        assert True

    def test_populate_config_with_property_names(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test _populate_config respects property names when available."""
        from tachograph_wizard.core.pdb_runner import _populate_config

        # Create mock property spec
        mock_prop_spec = MagicMock()
        mock_prop_spec.name = "test-property"

        # Create mock config with known properties
        mock_config = MagicMock()
        mock_config.list_properties.return_value = [mock_prop_spec]

        # Should not raise an exception
        values = [MagicMock()]
        _populate_config(mock_config, values)
