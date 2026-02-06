# pyright: reportPrivateUsage=false
"""Unit tests for template_exporter helper functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTemplateExporterHelpers:
    """Test pure/helper functions in template_exporter module."""

    def test_unwrap_value_with_get_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_unwrap_value calls get_value() when available."""
        from tachograph_wizard.core.template_exporter import _unwrap_value

        obj = MagicMock()
        obj.get_value.return_value = 42
        assert _unwrap_value(obj) == 42

    def test_unwrap_value_without_get_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_unwrap_value returns value as-is when no get_value."""
        from tachograph_wizard.core.template_exporter import _unwrap_value

        assert _unwrap_value(42) == 42
        assert _unwrap_value("hello") == "hello"

    def test_unwrap_value_with_failing_get_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_unwrap_value returns original when get_value raises."""
        from tachograph_wizard.core.template_exporter import _unwrap_value

        obj = MagicMock()
        obj.get_value.side_effect = Exception("fail")
        result = _unwrap_value(obj)
        assert result is obj

    def test_extract_result_values(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_extract_result_values extracts indexed values."""
        from tachograph_wizard.core.template_exporter import _extract_result_values

        result = MagicMock()
        result.index.side_effect = lambda i: [10, 20, 30][i] if i < 3 else (_ for _ in ()).throw(IndexError)  # type: ignore[arg-type]

        def side_effect(i: int) -> int:
            if i < 3:
                return [10, 20, 30][i]
            msg = "out of range"
            raise IndexError(msg)

        result.index.side_effect = side_effect
        values = _extract_result_values(result)
        assert values == [10, 20, 30]

    def test_extract_result_values_empty(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_extract_result_values returns empty list when index(0) fails."""
        from tachograph_wizard.core.template_exporter import _extract_result_values

        result = MagicMock()
        result.index.side_effect = IndexError("nothing")

        values = _extract_result_values(result)
        assert values == []

    def test_list_property_names(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_list_property_names extracts property names from GObject-like objects."""
        from tachograph_wizard.core.template_exporter import _list_property_names

        spec1 = MagicMock()
        spec1.name = "run-mode"
        spec2 = MagicMock()
        spec2.name = "layer"

        obj = MagicMock()
        obj.list_properties.return_value = [spec1, spec2]

        names = _list_property_names(obj)
        assert names == ["run-mode", "layer"]

    def test_list_property_names_no_method(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_list_property_names returns empty list when no list_properties."""
        from tachograph_wizard.core.template_exporter import _list_property_names

        result = _list_property_names(42)
        assert result == []

    def test_set_config_property_via_set_property(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_set_config_property uses set_property when available."""
        from tachograph_wizard.core.template_exporter import _set_config_property

        config = MagicMock()
        assert _set_config_property(config, "test", 42) is True
        config.set_property.assert_called_once_with("test", 42)

    def test_set_config_property_via_props(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_set_config_property falls back to props attribute."""
        from tachograph_wizard.core.template_exporter import _set_config_property

        config = MagicMock()
        config.set_property.side_effect = Exception("not available")
        config.props = MagicMock()

        assert _set_config_property(config, "test-prop", 42) is True

    def test_set_config_property_fails(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_set_config_property returns False when all methods fail."""
        from tachograph_wizard.core.template_exporter import _set_config_property

        config = MagicMock()
        config.set_property.side_effect = Exception("fail")
        config.props = None

        assert _set_config_property(config, "test", 42) is False


class TestExtractOffsets:
    """Test _extract_offsets function."""

    def test_tuple_with_bool_prefix(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Handle (success, x, y) tuple format."""
        from tachograph_wizard.core.template_exporter import _extract_offsets

        result = _extract_offsets((True, 100, 200))
        assert result == (100.0, 200.0)

    def test_tuple_two_values(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Handle (x, y) tuple format."""
        from tachograph_wizard.core.template_exporter import _extract_offsets

        result = _extract_offsets((50, 75))
        assert result == (50.0, 75.0)

    def test_object_with_offset_attrs(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Handle object with offset_x/offset_y attributes."""
        from tachograph_wizard.core.template_exporter import _extract_offsets

        obj = MagicMock()
        obj.offset_x = 30
        obj.offset_y = 40

        # Need to make sure it doesn't match tuple branch
        result = _extract_offsets(obj)
        assert result == (30.0, 40.0)

    def test_invalid_offsets_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises TemplateExportError for unreadable offsets."""
        from tachograph_wizard.core.template_exporter import TemplateExportError, _extract_offsets

        obj = MagicMock(spec=[])  # No attributes

        with pytest.raises(TemplateExportError, match="Unable to read layer offsets"):
            _extract_offsets(obj)


class TestColorHelpers:
    """Test _read_color_components and _color_to_hex."""

    @patch("tachograph_wizard.core.template_exporter.Gegl")
    def test_color_to_hex_from_rgba(
        self,
        mock_gegl: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Convert color with get_rgba to hex string."""
        from tachograph_wizard.core.template_exporter import _color_to_hex

        # Make isinstance(color, Gegl.Color) return True
        mock_gegl.Color = type("GeglColor", (), {})
        color = mock_gegl.Color()
        color.get_rgba = MagicMock(return_value=(1.0, 0.0, 0.5, 1.0))

        result = _color_to_hex(color)
        assert result == "#ff0080"

    @patch("tachograph_wizard.core.template_exporter.Gegl")
    def test_color_to_hex_black(
        self,
        mock_gegl: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Convert black color."""
        from tachograph_wizard.core.template_exporter import _color_to_hex

        mock_gegl.Color = type("GeglColor", (), {})
        color = mock_gegl.Color()
        color.get_rgba = MagicMock(return_value=(0.0, 0.0, 0.0, 1.0))

        result = _color_to_hex(color)
        assert result == "#000000"

    @patch("tachograph_wizard.core.template_exporter.Gegl")
    def test_color_to_hex_from_attributes(
        self,
        mock_gegl: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Convert color from r/g/b attributes when get_rgba is missing."""
        from tachograph_wizard.core.template_exporter import _color_to_hex

        mock_gegl.Color = type("GeglColor", (), {})
        color = mock_gegl.Color()
        color.r = 1.0
        color.g = 1.0
        color.b = 1.0

        result = _color_to_hex(color)
        assert result == "#ffffff"

    @patch("tachograph_wizard.core.template_exporter.Gegl")
    def test_read_color_components_non_color_raises(
        self,
        mock_gegl: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises TemplateExportError for non-Gegl.Color."""
        from tachograph_wizard.core.template_exporter import TemplateExportError, _read_color_components

        mock_gegl.Color = type("GeglColor", (), {})

        with pytest.raises(TemplateExportError, match="Unexpected color type"):
            _read_color_components("not a color")


class TestJustificationToAlign:
    """Test _justification_to_align function."""

    def test_center_justification(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """CENTER justification returns 'center'."""
        from tachograph_wizard.core.template_exporter import _justification_to_align

        obj = MagicMock()
        obj.name = "TEXT_JUSTIFY_CENTER"
        assert _justification_to_align(obj) == "center"

    def test_right_justification(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """RIGHT justification returns 'right'."""
        from tachograph_wizard.core.template_exporter import _justification_to_align

        obj = MagicMock()
        obj.name = "TEXT_JUSTIFY_RIGHT"
        assert _justification_to_align(obj) == "right"

    def test_left_justification(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """LEFT justification returns 'left'."""
        from tachograph_wizard.core.template_exporter import _justification_to_align

        obj = MagicMock()
        obj.name = "TEXT_JUSTIFY_LEFT"
        assert _justification_to_align(obj) == "left"

    def test_unknown_justification_defaults_to_left(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Unknown justification defaults to 'left'."""
        from tachograph_wizard.core.template_exporter import _justification_to_align

        assert _justification_to_align("UNKNOWN") == "left"


class TestIterLayersAndIsTextLayer:
    """Test _iter_layers and _is_text_layer functions."""

    def test_iter_layers_flat(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_iter_layers returns flat list of layers."""
        from tachograph_wizard.core.template_exporter import _iter_layers

        layer1 = MagicMock()
        layer1.get_children.return_value = []
        layer2 = MagicMock()
        layer2.get_children.return_value = []

        result = _iter_layers([layer1, layer2])
        assert len(result) == 2

    def test_iter_layers_with_children(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_iter_layers includes children recursively."""
        from tachograph_wizard.core.template_exporter import _iter_layers

        child = MagicMock()
        child.get_children.return_value = []

        parent = MagicMock()
        parent.get_children.return_value = [child]

        result = _iter_layers([parent])
        assert len(result) == 2  # parent + child

    @patch("tachograph_wizard.core.template_exporter.Gimp")
    def test_is_text_layer_with_text_layer_class(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_is_text_layer returns True when is_text_layer() returns True."""
        from tachograph_wizard.core.template_exporter import _is_text_layer

        # Set TextLayer to None to skip isinstance check
        mock_gimp.TextLayer = None

        layer = MagicMock()
        layer.is_text_layer.return_value = True

        assert _is_text_layer(layer) is True

    @patch("tachograph_wizard.core.template_exporter.Gimp")
    def test_is_text_layer_returns_false(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_is_text_layer returns False for non-text layer."""
        from tachograph_wizard.core.template_exporter import _is_text_layer

        mock_gimp.TextLayer = None

        layer = MagicMock()
        layer.is_text_layer.return_value = False

        assert _is_text_layer(layer) is False


class TestTemplateExporterParseLayerName:
    """Test TemplateExporter.parse_layer_name."""

    def test_valid_layer_name(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Parse 'text:field_name' correctly."""
        from tachograph_wizard.core.template_exporter import TemplateExporter

        assert TemplateExporter.parse_layer_name("text:driver") == "driver"
        assert TemplateExporter.parse_layer_name("Text:Vehicle") == "Vehicle"
        assert TemplateExporter.parse_layer_name("TEXT: field_1 ") == "field_1"

    def test_invalid_layer_name(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None for non-text layers."""
        from tachograph_wizard.core.template_exporter import TemplateExporter

        assert TemplateExporter.parse_layer_name("Layer 1") is None
        assert TemplateExporter.parse_layer_name("background") is None

    def test_empty_field_name(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when field name is empty after prefix."""
        from tachograph_wizard.core.template_exporter import TemplateExporter

        assert TemplateExporter.parse_layer_name("text:") is None
        assert TemplateExporter.parse_layer_name("text:  ") is None


class TestTemplateExporterExport:
    """Test TemplateExporter.export_template and related methods."""

    def test_export_template_empty_name_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        tmp_path: Path,
    ) -> None:
        """export_template raises for empty template name."""
        from tachograph_wizard.core.template_exporter import TemplateExporter, TemplateExportError

        exporter = TemplateExporter(mock_image)

        with pytest.raises(TemplateExportError, match="Template name is required"):
            exporter.export_template("", tmp_path / "out.json")

    def test_export_template_no_text_layers_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
        mock_image: MagicMock,
        tmp_path: Path,
    ) -> None:
        """export_template raises when no text layers found."""
        from tachograph_wizard.core.template_exporter import TemplateExporter, TemplateExportError

        mock_image.get_layers.return_value = []
        exporter = TemplateExporter(mock_image)

        with pytest.raises(TemplateExportError, match="No text layers"):
            exporter.export_template("test", tmp_path / "out.json")

    def test_template_to_dict(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_template_to_dict produces valid dictionary structure."""
        from tachograph_wizard.core.template_exporter import TemplateExporter
        from tachograph_wizard.templates.models import FontConfig, PositionConfig, Template, TextField

        template = Template(
            name="test",
            version="1.0",
            description="desc",
            reference_width=1000,
            reference_height=1000,
            fields={
                "driver": TextField(
                    position=PositionConfig(x_ratio=0.1, y_ratio=0.2),
                    font=FontConfig(family="Arial", size_ratio=0.05, color="#000000"),
                    align="left",
                    vertical_align="top",
                    visible=True,
                    required=False,
                ),
            },
        )

        result = TemplateExporter._template_to_dict(template)
        assert result["name"] == "test"
        assert "driver" in result["fields"]
        assert result["fields"]["driver"]["position"]["x_ratio"] == 0.1
        assert result["fields"]["driver"]["font"]["family"] == "Arial"


class TestCreateProcedureConfig:
    """Test _create_procedure_config function."""

    def test_create_config_via_proc(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Uses proc.create_config() when available."""
        from tachograph_wizard.core.template_exporter import _create_procedure_config

        proc = MagicMock()
        config = MagicMock()
        proc.create_config.return_value = config

        result = _create_procedure_config(proc)
        assert result is config

    @patch("tachograph_wizard.core.template_exporter.Gimp")
    def test_create_config_fails(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when all methods fail."""
        from tachograph_wizard.core.template_exporter import _create_procedure_config

        proc = MagicMock()
        proc.create_config.side_effect = Exception("fail")

        mock_gimp.ProcedureConfig = None

        result = _create_procedure_config(proc)
        assert result is None
